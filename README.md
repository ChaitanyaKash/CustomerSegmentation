# Customer Segmentation and E-Commerce Mining

## Overview

A customer analytics pipeline built for the **Data Warehouse and Mining Laboratory at NIT Sikkim**. The project brings together session data and fashion-catalogue metadata in a SQLite warehouse, constructs customer features, and applies segmentation, anomaly detection and predictive modelling.

The implementation covers source validation, temporal feature engineering, customer-level evaluation, model explainability and reproducible reporting.

**Authors:** Chaitanya Kashyap (B240006AI) and Aditya (B240030CS), Department of Computer Science and Engineering, National Institute of Technology Sikkim.

## Architecture

```text
E-commerce sessions + fashion catalogue
                  |
01_Data_Warehouse_ETL_updated.ipynb
  Source validation, calendar mapping and customer aggregation
                  |
SQLite warehouse
  fact_sessions
  dim_customer | dim_geography | dim_festival | dim_fashion_style
  mart_multimodal_customers
                  |
02_Multimodal_Data_Mining_updated.ipynb
  RFM segmentation | session anomalies | customer prediction | SHAP
                  |
Saved metrics, predictions, figures and project report
```

The fact table stores one row per session; the modelling mart stores one row per eligible customer. ETL checks cover unique keys, dimension coverage, nonnegative transaction values, date boundaries and database integrity. A future-data perturbation check verifies that changing future transactions does not change past customer features.

## Datasets

| Source | Size | Purpose |
| --- | --- | --- |
| `data/raw/Ecommerce.csv` | 25,000 sessions | Customer activity, transaction attributes and outcome construction |
| `data/raw/Fashion Dataset v2.csv` | 14,214 catalogue rows | Category-level price and rating metadata |
| `mart_multimodal_customers` | 7,875 customers | Customer features and future outcomes |

The supplied `Online Shopping Behavior Dataset.xlsx` is retained as a source file but is not joined because a shared customer key is undocumented. Source counts and hashes are recorded in [`outputs/etl_summary.json`](outputs/etl_summary.json).

## Methods

**Observation window:** sessions through 30 September 2024. **Outcome window:** the following 90 days, ending 29 December 2024. Predictors use observed activity available by the cutoff.

| Task | Definition | Approach |
| --- | --- | --- |
| Spending class | Future revenue: Low = 0, Medium = (0, 1000], High > 1000 | Logistic regression, XGBoost and LightGBM; macro-F1 selection |
| Future inactivity | No session during the outcome window | Logistic regression and random forest; average-precision selection |
| Revenue prediction | Revenue during the outcome window | Linear regression and raw/log-target gradient boosting; MAE selection |
| Segmentation | Patterns in observed recency, frequency and monetary value | Log1p RFM, standardisation and K-Means; silhouette and Davies-Bouldin diagnostics |
| Session anomalies | Unusual combinations of transaction and interaction attributes | Isolation Forest on six session features |

Customer features include session frequency, past spending, price and quantity aggregates, device/channel/payment/category shares, festival share, tenure, visit intervals and purchase/cart behaviour. Catalogue price, rating and normalised price supply category-level metadata proxies.

Evaluation uses a seed-42 stratified customer split: **6,300 training customers and 1,575 test customers**. Five-fold training CV selects models and hyperparameters. Imputation, scaling and SMOTE are fitted within CV training folds; weighting and resampling are compared under the same selection metric. Test customers do not participate in model selection.

Feature-group comparisons cover RFM, RFM with behaviour, and RFM with behaviour and catalogue proxies. SHAP explains the selected spending model using a training-customer sample. Exploratory nested validation uses three outer and five inner folds within the training partition to compare richer features, CatBoost, Extra Trees and decision weighting.

## Results

All scores below match printed notebook outputs and the saved metric exports.

### Spending prediction

Training CV selects **XGBoost with SMOTE**, using RFM, behavioural features and catalogue proxies. Each feature group uses its own CV-selected estimator.

| Features / baseline | Accuracy | Balanced accuracy | Macro-F1 | Low recall | Medium recall | High recall |
| --- | --- | --- | --- | --- | --- | --- |
| Majority baseline | 0.860317 | 0.333333 | 0.308305 | 1.000000 | 0.000000 | 0.000000 |
| Logistic regression baseline | 0.860317 | 0.333333 | 0.308305 | 1.000000 | 0.000000 | 0.000000 |
| RFM | 0.860317 | 0.333333 | 0.308305 | 1.000000 | 0.000000 | 0.000000 |
| RFM + behaviour | 0.719365 | 0.310229 | 0.311916 | 0.825830 | 0.012658 | 0.092199 |
| RFM + behaviour + proxies | 0.707302 | 0.319593 | 0.320110 | 0.808856 | 0.050633 | 0.099291 |

The model has a small macro-F1 advantage over the majority baseline, but lower accuracy and balanced accuracy. Medium and High recall remain low, limiting its usefulness for customer targeting.

![Spending confusion matrix](outputs/spending_confusion_matrix.png)

### Future inactivity

Training CV selects **logistic regression**. PR-AUC is measured as average precision. The prior baseline uses training prevalence and predicts the active class at the fixed threshold of 0.5.

| Model / baseline | ROC-AUC | PR-AUC (AP) | Churn F1 | Accuracy | Macro-F1 |
| --- | --- | --- | --- | --- | --- |
| Prior baseline | 0.500000 | 0.514286 | 0.000000 | 0.485714 | 0.326923 |
| Logistic regression | 0.471185 | 0.492620 | 0.500311 | 0.490159 | 0.489948 |

Ranking performance does not exceed the constant-score baseline on the test set.

### Revenue prediction

Training CV selects **gradient boosting with a log1p target** by MAE. Predictions are evaluated in the source revenue units.

| Model / baseline | R² | MAE |
| --- | --- | --- |
| Mean baseline | -0.000077 | 454.987265 |
| Linear regression | -0.011268 | 457.160529 |
| Gradient boosting / raw target | -0.009499 | 455.653103 |
| Gradient boosting / log1p | -0.095658 | 261.689656 |

The log-target model reduces MAE against the mean baseline, while negative R² indicates weak squared-error prediction. In nested validation, the training-median constant is selected in every outer fold, with mean MAE **267.732483**, matching the selected procedure. The zero-heavy target therefore requires a median reference when interpreting MAE.

### Training validation

The following spending scores are means across outer folds in the training partition. They are exploratory validation estimates and are reported separately from test scores.

| Procedure / baseline | Mean macro-F1 | Fold std | Mean accuracy | Mean balanced accuracy |
| --- | --- | --- | --- | --- |
| Majority baseline | 0.308397 | 0.000053 | 0.860794 | 0.333333 |
| Nested selected procedure | 0.316990 | 0.001800 | 0.785556 | 0.325481 |
| XGBoost recipe (fixed parameters) | 0.330954 | 0.015348 | 0.691111 | 0.336218 |

Broader candidate selection does not outperform the fixed XGBoost recipe in this comparison. Independent evaluation across another time window would be needed to assess temporal generalisation.

Detailed results: [model metrics](outputs/model_summary.json), [CV searches](outputs/spending_cv_search.csv), [nested validation](outputs/additional_validation_summary.json), and [cached customer predictions](outputs/heldout_predictions.csv).

## Insights

- **Customer profiles:** silhouette selection chooses six log-RFM segments within the tested K=2–6 range. Profiles distinguish recent buyers, less-recent buyers and visitors with no observed revenue. See the [segment profiles](outputs/segment_profiles.csv) and [selection diagnostics](outputs/segmentation_selection.csv).
- **Anomaly review:** Isolation Forest flags 250 of 25,000 sessions with contamination set to 0.01. These are statistical review candidates, not confirmed fraud labels.
- **Feature interpretation:** SHAP summarizes how the fitted spending model uses customer features. Attribution describes model behaviour rather than causal effects.
- **Predictive signal:** the spending distribution is dominated by zero future revenue. Accuracy, class-level recall and meaningful constant baselines are needed together to assess model utility.

![Customer segments in a PCA projection](outputs/rfm_segments.png)

Additional figures: [SHAP importance](outputs/spending_shap.png) and [session anomalies](outputs/session_anomalies.png).

## Limitations

The analysis uses one observation cutoff and one outcome horizon. Spending bands are illustrative; currency and business-specific thresholds need validation. The catalogue is undated and connected through an assumed category mapping rather than verified product-level joins. Some catalogue ratings and category coverage are missing.

Future inactivity measures observed session absence, and the revenue target covers 90 days rather than discounted lifetime value. Festival windows are manually defined. Geographic codes have undocumented meanings. Segment stability, causal marketing effects and production performance are not established. K=6 is at the boundary of the tested clustering range.

## How to run

Use **Python 3.12** from the repository root. `requirements.txt` contains direct dependency pins; `requirements-lock.txt` records the tested analysis environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
python scripts/run_notebooks.py
python scripts/verify_results.py
```

For interactive execution, launch `jupyter notebook` and run notebook 01 followed by notebook 02.

To build and verify the report from saved results:

```powershell
python -m pip install -r requirements-report.txt
python scripts/build_report.py
python scripts/verify_report.py
```

The verification scripts check customer separation, cached metrics, notebook execution, source hashes and report consistency. Building the report does not train models.

Read the [project report](Project_Report.pdf) or its [Markdown source](Project_Report.md) for the methodology and analysis. Generated metrics, predictions and figures are stored in `outputs/`.
