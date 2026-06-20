"""Check saved outputs without fitting models or reopening the holdout for tuning."""
import hashlib
import json
from pathlib import Path

import nbformat
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, recall_score
from sklearn.metrics import roc_auc_score, average_precision_score, r2_score, mean_absolute_error

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'


def verify():
    summary = json.loads((OUT / 'model_summary.json').read_text())
    text = ''
    for path in sorted(ROOT.glob('0*.ipynb')):
        notebook = nbformat.read(path, as_version=4)
        nbformat.validate(notebook)
        code = [cell for cell in notebook.cells if cell.cell_type == 'code']
        assert [cell.execution_count for cell in code] == list(range(1, len(code) + 1)), path.name
        for cell in code:
            assert not any(output.output_type == 'error' for output in cell.outputs)
            text += '\n'.join(output.get('text', '') for output in cell.outputs)
        print('PASS: fully executed notebook:', path.name)

    split = pd.read_csv(OUT / 'customer_split.csv')
    assert split.customer_id.is_unique
    train = split.loc[split.partition.eq('train'), 'customer_id']
    test = split.loc[split.partition.eq('test'), 'customer_id']
    assert set(train).isdisjoint(test)
    pred = pd.read_csv(OUT / 'heldout_predictions.csv')
    assert pred.customer_id.is_unique and set(pred.customer_id) == set(test)
    labels = ['Low', 'Medium', 'High']
    selected = summary['selection']
    spend = next(row for row in summary['spending'] if row['model'] == selected['spending_features'])
    actual = pred.consumption_class
    forecast = pred.predicted_spending_class
    measured = {'accuracy': accuracy_score(actual, forecast),
                'balanced_accuracy': balanced_accuracy_score(actual, forecast),
                'macro_f1': f1_score(actual, forecast, average='macro', zero_division=0)}
    measured.update(dict(zip(['recall_' + name for name in labels],
                             recall_score(actual, forecast, labels=labels, average=None, zero_division=0))))
    for name, value in measured.items():
        np.testing.assert_allclose(spend[name], value)
    churn = next(row for row in summary['churn'] if row['model'] == selected['churn_model'])
    np.testing.assert_allclose(churn['roc_auc'], roc_auc_score(pred.churn, pred.churn_probability))
    np.testing.assert_allclose(churn['pr_auc_ap'], average_precision_score(pred.churn, pred.churn_probability))
    np.testing.assert_allclose(churn['churn_f1'], f1_score(pred.churn, pred.churn_probability.ge(0.5)))
    clv = next(row for row in summary['clv'] if row['model'] == selected['clv_model'])
    np.testing.assert_allclose(clv['r2'], r2_score(pred.future_monetary, pred.predicted_future_revenue))
    np.testing.assert_allclose(clv['mae'], mean_absolute_error(pred.future_monetary, pred.predicted_future_revenue))
    print('PASS: selected-model metrics recomputed from cached holdout predictions')

    for key in ['spending', 'churn', 'clv']:
        saved = pd.read_csv(OUT / f'{key}_test_metrics.csv')
        pd.testing.assert_frame_equal(saved, pd.DataFrame(summary[key]), check_dtype=False)
        for row in summary[key]:
            for field, value in row.items():
                if isinstance(value, (float, int)):
                    assert f'{value:.6f}' in text, (key, field, value)
    print('PASS: every reported test metric is printed in the saved notebook')

    cv = pd.read_csv(OUT / 'spending_cv_search.csv')
    best = cv.loc[cv.cv_macro_f1.idxmax()]
    assert best.features == selected['spending_features']
    assert best.candidate == selected['spending_model']
    for group in cv.features.unique():
        assert len(cv.loc[cv.features.eq(group)]) == 5
    print('PASS: final spending choice matches train-only CV selection')

    extra_path = OUT / 'additional_validation_summary.json'
    if extra_path.exists():
        extra = json.loads(extra_path.read_text())
        assert extra['original_test_reopened'] is False
        for name, digest in extra['unchanged_original_evaluation_sha256'].items():
            assert hashlib.sha256((OUT / name).read_bytes()).hexdigest() == digest
        nested = pd.read_csv(OUT / 'additional_nested_cv_predictions.csv')
        assert nested.customer_id.is_unique and set(nested.customer_id) == set(train)
        folds = pd.read_csv(OUT / 'additional_nested_cv_folds.csv')
        for fold, group in nested.groupby('outer_fold'):
            for name, prediction_column in [('Nested selected procedure', 'nested_prediction'),
                ('Majority baseline', 'majority_prediction'), ('Original fixed recipe', 'original_recipe_prediction')]:
                row = folds.loc[folds.outer_fold.eq(fold) & folds.model.eq(name)].iloc[0]
                np.testing.assert_allclose(row.macro_f1, f1_score(group.actual, group[prediction_column], average='macro'))
                np.testing.assert_allclose(row.accuracy, accuracy_score(group.actual, group[prediction_column]))
                np.testing.assert_allclose(row.balanced_accuracy, balanced_accuracy_score(group.actual, group[prediction_column]))
        secondary = pd.read_csv(OUT / 'additional_secondary_nested_predictions.csv')
        for task, group in secondary.groupby('task'):
            assert group.customer_id.is_unique and set(group.customer_id) == set(train)
            scores = pd.read_csv(OUT / ('additional_churn_nested_folds.csv' if task == 'churn' else 'additional_revenue_nested_folds.csv'))
            for fold, predicted in group.groupby('outer_fold'):
                row = scores.loc[scores.outer_fold.eq(fold) & scores.model.eq('Nested selected procedure')].iloc[0]
                if task == 'churn':
                    np.testing.assert_allclose(row.roc_auc, roc_auc_score(predicted.actual, predicted.probability))
                    np.testing.assert_allclose(row.pr_auc_ap, average_precision_score(predicted.actual, predicted.probability))
                    np.testing.assert_allclose(row.churn_f1, f1_score(predicted.actual, predicted.prediction))
                else:
                    np.testing.assert_allclose(row.r2, r2_score(predicted.actual, predicted.prediction))
                    np.testing.assert_allclose(row.mae, mean_absolute_error(predicted.actual, predicted.prediction))
        for key in ['summary', 'churn_summary', 'revenue_summary']:
            for row in extra[key]:
                for field, value in row.items():
                    if isinstance(value, (float, int)):
                        assert f'{value:.6f}' in text, (key, field, value)
        print('PASS: nested validation uses training customers only, metrics match cached folds, original holdout unchanged')

    etl = json.loads((OUT / 'etl_summary.json').read_text())
    for name, expected in etl['source_sha256'].items():
        assert hashlib.sha256((ROOT / 'data/raw' / name).read_bytes()).hexdigest() == expected
    original = ROOT / 'local_notes/original_docs/Project_Report.pdf'
    if original.exists():
        assert hashlib.sha256(original.read_bytes()).hexdigest() == '54dd9600e564980df4d0e4eb46e2055bd47dae2dd819419912dd3270c4e363db'
    report_manifest = OUT / 'report_manifest.json'
    if report_manifest.exists():
        report = json.loads(report_manifest.read_text(encoding='utf-8'))
        assert hashlib.sha256((ROOT / 'Project_Report.pdf').read_bytes()).hexdigest() == report['report_sha256']
        assert hashlib.sha256((ROOT / 'Project_Report.md').read_bytes()).hexdigest() == report['markdown_sha256']
    print('PASS: raw sources and original-report backup unchanged; revised report matches manifest')
    assert not any(path.stat().st_size == 0 for path in OUT.iterdir() if path.is_file())
    print('All saved-result checks passed. No models were refitted.')


if __name__ == '__main__':
    verify()
