"""Build the report from saved results only; never fit or select a model here.

Run after the notebooks with: python scripts/build_report.py
PDF dependencies are pinned separately in requirements-report.txt.
"""
import csv
import hashlib
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab import __version__ as reportlab_version
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                               TableStyle, PageBreak, Image)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'
REVISION = '27 October 2026'
ORIGINAL_REPORT_SHA256 = '54dd9600e564980df4d0e4eb46e2055bd47dae2dd819419912dd3270c4e363db'
NAVY = colors.HexColor('#183349')
TEAL = colors.HexColor('#087e8b')
INK = colors.HexColor('#223645')
LIGHT = colors.HexColor('#eff5f8')
WIDTH = A4[0] - 96


def load_json(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


def load_csv(name):
    with (OUT / name).open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    results = load_json('model_summary.json')
    extra = load_json('additional_validation_summary.json')
    etl = load_json('etl_summary.json')
    legacy = load_json('legacy_audit.json')
    original = ROOT / 'local_notes/original_docs/Project_Report.pdf'
    # Preserve the original before replacing the public PDF; never overwrite its backup.
    if original.exists():
        assert digest(original) == ORIGINAL_REPORT_SHA256
    elif digest(ROOT / 'Project_Report.pdf') == ORIGINAL_REPORT_SHA256:
        original.parent.mkdir(parents=True, exist_ok=True)
        original.write_bytes((ROOT / 'Project_Report.pdf').read_bytes())

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('ReportTitle', fontName='Helvetica-Bold', fontSize=27,
        leading=32, textColor=NAVY, spaceAfter=20))
    styles.add(ParagraphStyle('ReportSub', fontName='Helvetica', fontSize=12,
        leading=17, textColor=TEAL, spaceAfter=16))
    styles.add(ParagraphStyle('ReportH1', fontName='Helvetica-Bold', fontSize=17,
        leading=22, textColor=NAVY, spaceAfter=12))
    styles.add(ParagraphStyle('ReportH2', fontName='Helvetica-Bold', fontSize=11,
        leading=15, textColor=TEAL, spaceBefore=9, spaceAfter=6))
    styles.add(ParagraphStyle('ReportBody', fontName='Helvetica', fontSize=9.2,
        leading=13.4, textColor=INK, spaceAfter=8))
    styles.add(ParagraphStyle('ReportCaption', fontName='Helvetica', fontSize=8,
        leading=11, textColor=INK, spaceAfter=9))
    styles.add(ParagraphStyle('ReportCode', fontName='Courier', fontSize=8,
        leading=12, textColor=INK, backColor=LIGHT, borderPadding=8, spaceAfter=10))
    story, markdown, numeric_values = [], [], []

    def rich(text):
        text = escape(str(text))
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', text)
        return text

    def p(text, style='ReportBody'):
        story.append(Paragraph(rich(text), styles[style]))
        markdown.extend([text, ''])

    def h(text, level=1):
        story.append(Paragraph(rich(text), styles['ReportH1' if level == 1 else 'ReportH2']))
        markdown.extend([('#' * (level + 1)) + ' ' + text, ''])

    def page(title):
        story.append(PageBreak())
        markdown.extend(['<!-- pagebreak -->', ''])
        h(title)

    def tab(headers, rows, widths=None, font_size=8):
        body_style = ParagraphStyle('TableBody', fontName='Helvetica', fontSize=font_size,
                                    leading=font_size + 3, textColor=INK)
        head_style = ParagraphStyle('TableHeader', parent=body_style, fontName='Helvetica-Bold', textColor=colors.white)
        rendered = [[Paragraph(rich(value), head_style) for value in headers]]
        rendered += [[Paragraph(rich(value), body_style) for value in row] for row in rows]
        table = Table(rendered, colWidths=widths, repeatRows=1, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, NAVY),
            ('LINEBELOW', (0, -1), (-1, -1), 0.4, colors.HexColor('#c6d5df'))]))
        story.extend([table, Spacer(1, 9)])
        markdown.extend(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |'])
        markdown.extend('| ' + ' | '.join(map(str, row)) + ' |' for row in rows)
        markdown.append('')

    def metric_table(rows, fields, widths=None, font_size=8):
        values = []
        for row in rows:
            values.append([])
            for key, title in fields:
                value = row[key]
                if isinstance(value, (int, float)):
                    value = f'{value:.6f}'
                    numeric_values.append(value)
                values[-1].append(value)
        tab([title for key, title in fields], values, widths, font_size)

    def figure(name, caption, width=440):
        path = OUT / name
        w, height = ImageReader(str(path)).getSize()
        image = Image(str(path), width=width, height=width * height / w)
        image.hAlign = 'CENTER'
        story.extend([image, Spacer(1, 5), Paragraph(rich(caption), styles['ReportCaption'])])
        markdown.extend([f'![{caption}](outputs/{name})', ''])

    # Page 1: scope and evidence, with the real report revision date.
    story.append(Spacer(1, 24))
    p('NATIONAL INSTITUTE OF TECHNOLOGY SIKKIM', 'ReportSub')
    p('Customer Segmentation<br/>and E-Commerce Mining'.replace('<br/>', '\n'), 'ReportTitle')
    markdown[2:2] = ['# Customer Segmentation and E-Commerce Mining', '']
    p('Data Warehouse and Mining Laboratory (AI14201 / CS14211)', 'ReportSub')
    p('Submitted by **Chaitanya Kashyap (B240006AI)** and **Aditya (B240030CS)**.')
    p('Submitted to **Dr. Krishna Kumar, Assistant Professor**, Department of Computer Science and Engineering.')
    p('Revised report: **' + REVISION + '**. This revision supersedes the original report and reports the results of the saved notebooks.')
    h('Abstract', 2)
    p('This project builds a SQLite session warehouse and evaluates future spending class, future session inactivity and next-period revenue. A fixed customer holdout and training-only cross-validation separate model selection from final evaluation. Descriptive mining uses log-transformed RFM and multivariate session anomaly detection.')
    p('The audit exposed arbitrary row-order tie breaking in spending labels, unsupported historical claims and a same-period revenue target. This revision uses declared future-revenue bands, a fully observed 90-day inactivity horizon, and a next-90-day revenue target. These changes make old and new scores non-comparable.')
    p('The resulting predictive evidence is weak. Spending macro-F1 is only slightly above a majority baseline, churn ranking is weak, and lower revenue MAE than a mean baseline is explained by zero-heavy outcomes. A broader training-only nested-validation search did not establish a stronger model. The contribution is an auditable pipeline and an honest assessment of its limits.')
    tab(['Scope', 'Evidence'], [
        ['Data', f"{etl['sessions']:,} sessions; {etl['catalogue_rows']:,} catalogue rows; {etl['customers']:,} eligible customers"],
        ['Feature cutoff', etl['cutoff']], ['Outcome horizon end', etl['horizon_end']],
        ['Reporting rule', 'Every reported model score comes from a saved notebook output.']], [120, WIDTH - 120])

    page('1. Data architecture and ETL')
    p('The repository retains two notebooks: notebook 01 validates and loads sources; notebook 02 performs modelling and descriptive mining. The supplied workbook is retained but is not joined because a shared customer identifier is undocumented.')
    tab(['Source', 'Verified use'], [
        ['Ecommerce.csv', '25,000 session records with dates, revenue, device, payment, channel, category and interaction attributes.'],
        ['Fashion Dataset v2.csv', '14,214 catalogue rows. Category-level price and rating aggregates provide metadata proxies.'],
        ['Online Shopping Behavior Dataset.xlsx', 'Retained unchanged; not used for modelling or unsupported customer-level joins.']], [180, WIDTH - 180])
    h('Star-schema tables', 2)
    tab(['Table', 'Grain / role'], [
        ['fact_sessions', 'One row per session; all 25,000 sessions are retained.'],
        ['dim_customer', 'Source customer identifiers; no fabricated slowly changing history.'],
        ['dim_geography', 'Undocumented source location codes, without invented Indian states.'],
        ['dim_festival', 'Manual 2024 festival windows; first matching window wins on overlap.'],
        ['dim_fashion_style', 'Category price/rating metadata and proxy coverage.'],
        ['mart_multimodal_customers', 'One row per eligible customer; past predictors and separately named future outcomes.']], [180, WIDTH - 180])
    h('Time window and outcomes', 2)
    p('Past features use visits on or before 30 September 2024. Outcomes use visits after that cutoff through 29 December 2024 inclusive, a 90-day horizon. Customers first seen after the cutoff do not enter the modelling population. The final source date outside the horizon is excluded from labels.')
    tab(['Spending band', 'Future revenue rule', 'Customers'], [
        ['Low', 'Exactly zero', str(etl['class_counts']['Low'])],
        ['Medium', 'Positive and at most 1,000', str(etl['class_counts']['Medium'])],
        ['High', 'Above 1,000', str(etl['class_counts']['High'])]], [100, 280, WIDTH - 380])
    p('These fixed bands are illustrative, not business-validated thresholds; the source currency is undocumented. Identical future revenue receives identical labels, unlike the old row-order ranking rule.')

    page('2. Feature design and evaluation protocol')
    h('Customer split', 2)
    p('A seed-42 stratified split is fixed before any initial model fit: 6,300 training and 1,575 test customers, with no customer overlap. The same customer partition is reused for spending, churn and revenue. Spending stratification does not imply separate churn stratification of the outer holdout.')
    tab(['Partition', 'Low', 'Medium', 'High', 'Total'], [
        ['Train', '5,423', '315', '562', '6,300'], ['Test', '1,355', '79', '141', '1,575']],
        [119, 95, 95, 95, WIDTH - 404])
    h('Predictor groups', 2)
    tab(['Group', 'Features and rationale'], [
        ['RFM', 'Recency, distinct session frequency and past monetary sum. Past spending is allowed because the target is future revenue.'],
        ['Behaviour', 'Session count; average/median unit price; quantity; device, channel, payment and category shares; festival share; tenure; visit intervals; purchase/cart shares and discounts.'],
        ['Catalogue proxies', 'Observed-category-weighted catalogue price, average rating, normalised price and coverage. No images are processed.'],
        ['Further validation', 'Recent 30/60/90/180-day counts and spending, trends, purchase timing, last-session attributes and calendar summaries. The expanded set has 99 predictors.']], [120, WIDTH - 120])
    h('Leakage controls', 2)
    p('Future monetary, future session count, churn, class labels and customer IDs are excluded from predictors. Features use past visits only. A perturbation of future revenue, unit price and device data must leave every past feature unchanged. Source keys, nonnegative values, dimension coverage and SQLite integrity are checked.')
    p('Initial model selection uses five-fold training CV. Median imputation, scaling and optional SMOTE occur inside each fold. XGBoost sample weights are recomputed on the fold training labels; LightGBM class weights are fold-local. Randomised searches maximise macro-F1 for spending. No held-out threshold, feature or model selection occurs.')
    p('After all initial supervised selections are locked, each prespecified estimator is evaluated in one final test stage. Later figures and error inspection use cached predictions. Further development uses nested validation on original training customers only, with hashes proving that original test outputs remain unchanged.')
    h('Selection budgets and compute', 2)
    p('Each spending tree family/imbalance approach samples four configurations, and logistic regression samples three. Searches use one CV job and two native CPU threads. Temperature monitoring is external; pause at 75 degrees C and remain below 85 degrees C. No GPU training is used.')

    page('3. Spending prediction and ablation')
    p('Training CV selected XGBoost with SMOTE and RFM + behavioural + catalogue-proxy features. Each ablation selects its own estimator using the same candidate families and search budget; the comparison therefore measures modelling recipes rather than a causal proxy effect.')
    metric_table(results['spending'], [
        ('model', 'Recipe / baseline'), ('accuracy', 'Accuracy'), ('balanced_accuracy', 'Balanced accuracy'),
        ('macro_f1', 'Macro-F1'), ('recall_Low', 'Low recall'), ('recall_Medium', 'Medium recall'),
        ('recall_High', 'High recall')], [139] + [(WIDTH - 139) / 6] * 6, 7.1)
    p('Scores above are final held-out results. The selected model raises macro-F1 slightly above the majority baseline while losing accuracy and balanced accuracy. It recalls few Medium or High customers; the evidence does not support strong targeting performance.')
    figure('spending_confusion_matrix.png', 'Figure 1. Locked spending model on held-out customers; rows are actual classes and columns are predictions.', width=280)
    p('The 14 Medium customers predicted High are an error cohort, not validated aspirational prospects. No in-sample marketing target list is produced. The unsupported fixed +6% visual improvement claim is replaced by the measured ablation above.')
    p('Source: outputs/spending_test_metrics.csv and outputs/spending_confusion_matrix.csv.', 'ReportCaption')

    page('4. Future inactivity and revenue prediction')
    h('Churn: no session in the next 90 days', 2)
    p('The old churn rule, recency above 90 days, is replaced with absence of sessions in the future horizon. Logistic regression and random forest are compared by training-CV average precision. Logistic regression wins that selection. The original test decision threshold remains 0.5; PR-AUC here means average precision.')
    metric_table(results['churn'], [('model', 'Model / baseline'), ('roc_auc', 'ROC-AUC'),
        ('pr_auc_ap', 'PR-AUC (AP)'), ('churn_f1', 'Churn F1'), ('accuracy', 'Accuracy'),
        ('macro_f1', 'Macro-F1')], [139] + [(WIDTH - 139) / 5] * 5, 7.5)
    p('The model ranks worse than the constant-score baseline on this holdout. The prior baseline uses training prevalence; at 0.5 it predicts the active class, so its zero churn F1 is a weak F1 reference. The later nested analysis adds an always-churn reference. Session absence is not confirmed account closure.')
    h('CLV proxy: next-90-day revenue', 2)
    p('Past features predict future monetary revenue, rather than explaining the same-period monetary column. Linear regression and raw/log1p-target histogram gradient boosting are compared by training-CV MAE on the original revenue scale. The log-target model is selected; inverse predictions use expm1 without a smearing correction.')
    metric_table(results['clv'], [('model', 'Model / baseline'), ('r2', 'R-squared'), ('mae', 'MAE')],
                 [WIDTH - 190, 95, 95])
    p('The selected model improves MAE relative to a mean predictor, but its negative R-squared indicates weak squared-error forecasting. With mostly zero outcomes, a near-zero estimate can improve MAE without learning useful revenue separation. The nested analysis tests this against a median constant. This target is not discounted lifetime value.')
    p('Sources: outputs/churn_test_metrics.csv and outputs/clv_test_metrics.csv.', 'ReportCaption')

    page('5. Additional training-only validation')
    p('After the original holdout was opened, a requested second round explored stronger models without reopening it. Three outer folds assess a procedure with five inner folds. All customers in this extension belong to the original training partition. Estimates remain exploratory because algorithm development has already used this population; a new future period is still required.')
    h('Spending: richer features and decision weighting', 2)
    p('Compare logistic regression, Extra Trees, histogram boosting, CatBoost at two depths, and the original fixed XGBoost recipe. Inner out-of-fold probabilities choose the candidate and class multipliers by macro-F1. Each locked choice is evaluated once on its outer fold. Multipliers are decision weights, not calibrated probabilities.')
    metric_table(extra['summary'], [('model', 'Procedure / reference'), ('macro_f1_mean', 'Mean macro-F1'),
        ('macro_f1_std', 'Fold std'), ('accuracy_mean', 'Mean accuracy'),
        ('balanced_accuracy_mean', 'Mean balanced accuracy')], [167] + [(WIDTH - 167) / 4] * 4, 7.5)
    p('The broader selection does not outperform the original recipe on these outer folds. That recipe was previously chosen using the full training set, so it is an exploratory reference, not an independently selected nested competitor. Inner full-training selection is optimistic and does not justify promoting a new model.')
    h('Churn: ranking and threshold selection', 2)
    metric_table(extra['churn_summary'], [('model', 'Procedure / reference'), ('roc_auc_mean', 'Mean ROC-AUC'),
        ('pr_auc_ap_mean', 'Mean PR-AUC (AP)'), ('churn_f1_mean', 'Mean churn F1')], [199, 100, 100, WIDTH - 399], 7.5)
    p('Ranking remains near chance. Threshold tuning produces approximately the always-churn reference F1, rather than meaningful customer separation.')
    h('Revenue: test the median reference', 2)
    metric_table(extra['revenue_summary'], [('model', 'Procedure / reference'), ('r2_mean', 'Mean R-squared'),
        ('mae_mean', 'Mean MAE')], [WIDTH - 190, 95, 95])
    p('The training-median constant wins inner selection in every outer fold. Extra modelling did not beat this simple reference. These validation means must not be subtracted from held-out scores to claim an improvement.')

    page('6. Log-RFM customer segmentation')
    p('Recency, frequency and monetary are log1p-transformed and standardised before K-Means. K is selected from 2 through 6 using the highest silhouette on a fixed sample of up to 2,000 customers. Davies-Bouldin and inertia are diagnostics. Gaussian-mixture BIC is a separate model-family diagnostic, not a K-Means score.')
    diagnostics = load_csv('segmentation_selection.csv')
    metric_table([{key: (int(value) if key == 'k' else float(value)) for key, value in row.items()} for row in diagnostics],
        [('k', 'K'), ('silhouette', 'Silhouette'), ('davies_bouldin', 'Davies-Bouldin'), ('gmm_bic', 'GMM BIC')],
        [50, 135, 145, WIDTH - 330])
    h('Selected segment profiles', 2)
    profiles = load_csv('segment_profiles.csv')
    tab(['ID', 'Customers', 'Mean recency', 'Mean frequency', 'Mean monetary', 'Median monetary'],
        [[row['segment'], row['customers'], *[f"{float(row[key]):.2f}" for key in
          ['recency_mean', 'frequency_mean', 'monetary_mean', 'monetary_median']]] for row in profiles],
        [35, 65, 90, 100, 104, WIDTH - 394], 7.6)
    p('K=6 wins silhouette within the tested range and also has the lowest tested GMM BIC. Because the optimum is at the search boundary, it does not establish six natural or stable customer types. IDs describe past activity; labels such as VIP or sleepers are not validated business outcomes.')
    figure('rfm_segments.png', 'Figure 2. PCA projection of the descriptive log-RFM segments; all eligible customers are included.', width=330)

    page('7. Explainability and model interpretation')
    p('SHAP explains the locked initial spending classifier on a deterministic sample of 150 training customers. Imputation and scaling use the fitted training pipeline. The explanation never selects features from test outcomes. Tree models use TreeExplainer; linear models use LinearExplainer if selected.')
    figure('spending_shap.png', 'Figure 3. Mean absolute SHAP attribution across sampled training customers and output classes.', width=470)
    p('The displayed predictors describe how this particular fitted model uses its inputs. A high attribution does not show causation, predictive reliability, campaign lift or customer intent. The weak held-out metrics remain the main evidence of utility.')
    p('Catalogue price, average rating and normalised price are metadata aggregates, weighted by past category preferences. The category mapping is assumed, product joins are unverified, and missing categories are not filled with future session statistics. No ResNet-50 embeddings, PyTorch image pipeline or verified visual-feature uplift is present.')
    p('Sources: outputs/spending_shap_importance.csv and the saved SHAP figure from notebook 02.', 'ReportCaption')

    page('8. Multivariate session anomalies and limitations')
    p('Isolation Forest uses log1p revenue, unit price, quantity, pages viewed, time on site and discount percentage. It is fitted descriptively on all 25,000 sessions, separately from predictive modelling. Configured contamination is 0.01; 250 sessions are flagged.')
    figure('session_anomalies.png', 'Figure 4. Session revenue versus time on site; red points are multivariate anomaly flags, not verified fraud.', width=445)
    p('Flags are statistical unusualness under a specified detector. The chosen contamination controls the approximate flag rate; it is not detection accuracy. There are no confirmed fraud or bot labels and no claim of validated fraud detection.')
    h('Practical limits', 2)
    p('One cutoff cannot establish temporal generalisation. Revenue bands are illustrative, the currency is undocumented and zero outcomes dominate spending and revenue. Catalogue dates and cross-source identity are unknown. Geography codes have no verified state mapping. Festival windows are manually curated and do not support causal promotion-effect claims.')
    p('The warehouse is an educational SQLite implementation. Segment stability, model calibration, economic value and deployment performance have not been established. New verified customer/product links, stronger historical signals and a genuinely untouched future period are needed before making operational recommendations.')

    page('9. Corrected claims and conclusion')
    tab(['Historical claim / issue', 'Current evidence'], [
        ['Approximately 88% churn accuracy', 'Unsupported. The old saved notebook printed 0.63 accuracy; the new future-inactivity results are reported with ranking metrics and baselines.'],
        ['ResNet-50 visual embeddings', 'Absent. The implementation uses catalogue category-level price/rating proxies.'],
        ['Fixed +6% visual-feature gain', 'Unsupported. A measured feature-group ablation replaces the claim; it does not establish causal or statistically significant uplift.'],
        ['Old macro-F1 approximately 0.454', 'The saved XGBoost macro-F1 is 0.455329; 0.454055 is balanced accuracy.'],
        ['14,000 catalogue products', 'The source contains 14,214 rows. This is not a verified cross-source product join.'],
        ['Balanced future-spending classes', 'Row-order tie breaking split identical zero revenue across classes. Declared bands replace that arbitrary target.'],
        ['Aspirational marketing targets', 'Medium-to-High misclassification is an error cohort, not demonstrated marketing opportunity.'],
        ['Geographic, festival or fraud conclusions', 'No invented state mapping, causal festival lift or validated fraud detection is claimed.']], [169, WIDTH - 169], 8)
    h('Historical versus current evaluation', 2)
    old_xgb = next(row for row in legacy['spending'] if row['model'] == 'XGBoost')
    current_xgb = next(row for row in results['spending'] if row['model'] == results['selection']['spending_features'])
    current_churn = next(row for row in results['churn'] if row['model'] == results['selection']['churn_model'])
    current_revenue = next(row for row in results['clv'] if row['model'] == results['selection']['clv_model'])
    tab(['Metric', 'Historical saved output', 'Current held-out output'], [
        ['Spending accuracy / macro-F1', f"{old_xgb['accuracy']:.6f} / {old_xgb['macro_f1']:.6f}",
         f"{current_xgb['accuracy']:.6f} / {current_xgb['macro_f1']:.6f}"],
        ['Churn accuracy / macro-F1', f"{legacy['churn']['accuracy']:.2f} / {legacy['churn']['macro_f1']:.2f} (saved precision)",
         f"{current_churn['accuracy']:.6f} / {current_churn['macro_f1']:.6f}"],
        ['Revenue R-squared', f"{legacy['clv']['r2']:.4f}", f"{current_revenue['r2']:.6f}"]], [170, 165, WIDTH - 335], 8)
    p('These rows are historical context, not a controlled before/after experiment. Spending labels, churn labels, revenue targets and customer splitting changed. A higher spending accuracy cannot be advertised as a genuine improvement across those different tasks.')
    h('Conclusion', 2)
    p('The revision delivers a reproducible warehouse, explicit future outcomes, fold-local training, auditable baselines and saved evidence. Additional model complexity did not establish a stronger predictive model. Honest limitations and a reproducible negative result are preferable to unsupported performance or business claims.')

    page('10. Reproduction and evidence index')
    p('The report is generated from saved notebook exports. Building it does not refit a model, reopen the test set or modify saved scores. The original report is preserved under local_notes/original_docs/ and excluded from Git. Its SHA-256 is recorded in the report manifest.')
    h('Run the analysis', 2)
    p('Use Python 3.12 on Windows. Create and activate a virtual environment, then install the pinned analysis environment. Run commands from the repository root.')
    for command in ['python -m pip install -r requirements-lock.txt', 'python scripts/run_notebooks.py',
                    'python scripts/verify_results.py', 'python -m pip install -r requirements-report.txt',
                    'python scripts/build_report.py', 'python scripts/verify_report.py']:
        p(command, 'ReportCode')
    p('The runner uses the current Python executable, executes both notebooks sequentially and saves outputs. Monitor temperature externally; thermal.pause pauses between fits. Interrupt immediately if needed during a fit. Do not run concurrent training jobs.')
    h('Evidence index', 2)
    tab(['Artifact', 'Role'], [
        ['01_Data_Warehouse_ETL_updated.ipynb', 'Source validation, temporal mart, warehouse and leakage checks.'],
        ['02_Multimodal_Data_Mining_updated.ipynb', 'Initial training selection, final test, explanations, descriptive mining and separate nested validation.'],
        ['outputs/model_summary.json', 'Authoritative initial held-out model metrics.'],
        ['outputs/additional_validation_summary.json', 'Training-only nested estimates and unchanged holdout hashes.'],
        ['outputs/legacy_audit.json', 'Historical saved-output audit with source commit.'],
        ['outputs/customer_split.csv', 'Fixed, customer-disjoint train/test partition.'],
        ['outputs/*_test_metrics.csv', 'Per-model held-out scores; cached predictions support verification.'],
        ['Project_Report.md / scripts/build_report.py', 'Readable report source and reproducible PDF builder.'],
        ['outputs/report_manifest.json', 'Source/output hashes, numerical reporting checks and report build versions.']],
        [230, WIDTH - 230], 7.8)
    p('Project repository: https://github.com/ChaitanyaKash/CustomerSegmentation. References in this report are repository artifacts, not claims about unverified external dataset provenance. Slides were absent from the repository; their location remains unresolved and no updated slide deck is claimed.', 'ReportCaption')

    markdown_path = ROOT / 'Project_Report.md'
    markdown_path.write_text('\n'.join(markdown), encoding='utf-8')

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#ccd9e1'))
        canvas.line(48, 40, A4[0] - 48, 40)
        canvas.setFont('Helvetica', 7.5)
        canvas.setFillColor(INK)
        canvas.drawString(48, 27, 'Customer Segmentation | Revised ' + REVISION)
        canvas.drawRightString(A4[0] - 48, 27, str(doc.page))
        if doc.page > 1:
            canvas.setFillColor(TEAL)
            canvas.setFont('Helvetica-Bold', 8)
            canvas.drawString(48, A4[1] - 29, 'NIT SIKKIM | DATA WAREHOUSE AND MINING LABORATORY')
        canvas.restoreState()

    pdf = ROOT / 'Project_Report.pdf'
    doc = SimpleDocTemplate(str(pdf), pagesize=A4, rightMargin=48, leftMargin=48,
                            topMargin=49, bottomMargin=52,
                            title='Customer Segmentation and E-Commerce Mining - Revised Report',
                            author='Chaitanya Kashyap and Aditya', subject='Leakage-safe evaluation and saved project results')
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    sources = ['etl_summary.json', 'model_summary.json', 'additional_validation_summary.json',
               'legacy_audit.json', 'segment_profiles.csv', 'segmentation_selection.csv',
               'spending_confusion_matrix.png', 'spending_shap.png', 'rfm_segments.png', 'session_anomalies.png']
    manifest = {'revision': REVISION, 'report_sha256': digest(pdf), 'markdown_sha256': digest(markdown_path),
        'original_report_sha256': ORIGINAL_REPORT_SHA256, 'reportlab_version': reportlab_version,
        'source_sha256': {name: digest(OUT / name) for name in sources},
        'reported_numeric_values': sorted(set(numeric_values)), 'models_refitted': False}
    (OUT / 'report_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('Built:', pdf)
    print('Report source:', markdown_path)
    print('No models were fitted or evaluated.')


if __name__ == '__main__':
    build()
