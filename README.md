# 🛒 Customer Segmentation & E-Commerce Mining
An end-to-end **Data Warehousing and Data Mining** project that analyzes Indian e-commerce customer behavior to identify spending patterns, segment customers, and predict spending classes using machine learning.

> **Built as part of the Data Warehouse & Mining Laboratory course at NIT Sikkim.**

---

## 📌 Overview

This project implements the complete **Data Warehousing and Data Mining (DWM) lifecycle**, starting from raw data extraction and ETL to building a star schema warehouse, performing OLAP analysis, customer segmentation, anomaly detection, churn prediction, and spending-class prediction.

The objective is to help e-commerce businesses understand customer behavior and make data-driven marketing decisions.

---

## 🚀 Features

### 📊 Data Warehousing & ETL

* Extract and preprocess multiple datasets
* Data cleaning and transformation
* SQLite-based Star Schema implementation
* RFM (Recency, Frequency, Monetary) feature engineering
* Festival-aware feature engineering
* Data quality validation

### 📈 Exploratory Data Analysis

* Spending class distribution
* Correlation heatmaps
* OLAP-style dashboards
* Revenue time-series analysis
* Cohort retention analysis
* Geographic spending analysis
* Festival impact visualization

### 👥 Customer Segmentation

* K-Means Clustering
* Hierarchical Clustering
* DBSCAN
* Gaussian Mixture Models (GMM)
* PCA visualization
* t-SNE visualization
* Segment profiling

### 🔍 Advanced Data Mining

* Isolation Forest anomaly detection
* Customer churn prediction
* Customer Lifetime Value (CLV) regression

### 🤖 Predictive Modeling

* Spending class prediction
* SMOTE for class balancing
* XGBoost classifier
* Feature importance analysis
* SHAP explainability

---

# 🏗️ Data Warehouse Architecture

The project follows a **Star Schema** consisting of:

## Fact Table

* `fact_sessions`

## Dimension Tables

* `dim_customer`
* `dim_geography`
* `dim_festival`
* `dim_fashion_style`

The warehouse enables efficient OLAP-style analytics and business intelligence reporting.

---

# 📂 Datasets

| Dataset             | Size            | Purpose                                  |
| ------------------- | --------------- | ---------------------------------------- |
| E-Commerce Sessions | 25,000 records  | Customer behavioral data                 |
| Fashion Catalogue   | 14,000 products | Product metadata & visual proxy features |

The datasets include:

* Revenue
* Device Type
* Payment Method
* Marketing Channel
* Product Ratings
* Brand Information
* Price
* Color Features

---

# 🛠️ Tech Stack

* Python
* Pandas
* NumPy
* SQLite
* Scikit-learn
* XGBoost
* Matplotlib
* Seaborn
* SHAP
* PyTorch
* Jupyter Notebook

---

# 🤖 Machine Learning Models

## Clustering

* K-Means
* Hierarchical Clustering
* DBSCAN
* Gaussian Mixture Model (GMM)

## Anomaly Detection

* Isolation Forest

## Classification

* Random Forest
* XGBoost

## Regression

* Linear Regression (Customer Lifetime Value)

---

# 📊 Key Results

✅ Built a complete ETL pipeline and star-schema warehouse

✅ Identified three meaningful customer segments:

* ⭐ Stars (VIP Customers)
* 👤 Regular Customers
* 😴 Sleepers

✅ Festival periods showed significantly higher average spending

✅ Isolation Forest successfully detected high-value outliers and bot-like behavior

✅ Churn prediction achieved approximately **88% accuracy**

✅ XGBoost spending-class prediction achieved approximately **54% accuracy**

✅ Visual proxy features improved model performance by **~6%**

---

# 📁 Project Structure

```text
Customer-Segmentation-Ecommerce-Mining/
│
├── data/
│   ├── raw/
│   │   ├── Ecommerce.csv
│   │   ├── Fashion Dataset v2.csv
│   │   └── Online Shopping Behavior Dataset.csv
│   │
│   └── warehouse/
│       └── indian_multimodal_warehouse.db
│
├── outputs/
│
├── 01_Data_Warehouse_ETL_update.ipynb
├── 02_Multimodal_Data_Mining_update.ipynb
├── Project_Report.pdf
├── README.md
```

---

# 📈 Business Insights

* High-frequency customers generate a disproportionate share of revenue.
* Festival campaigns significantly increase customer spending.
* Direct traffic users are more likely to become high-value customers.
* Mobile dominates traffic, while desktop users tend to spend more per purchase.
* VIP customers should receive personalized retention strategies.
* Early churn intervention can substantially improve customer lifetime value.

---

## ⚠️ Limitations

* The project is based on a dataset containing approximately **25,000 customer sessions**, which may not fully capture the diversity and scale of real-world e-commerce platforms handling millions of users.
* Geographic analysis uses simulated state mappings due to the absence of actual customer location data.
* Visual features are approximated using category-level proxy attributes rather than detailed image embeddings for every product.
* Customer spending classes (Low, Medium, High) are generated using quantile-based segmentation and may differ from business-specific definitions.
* The XGBoost classifier achieves moderate accuracy (~54%), suggesting that additional features or larger datasets could improve predictive performance.
* Festival and promotional event analysis relies on a manually curated calendar and may not capture all platform-specific sales or flash events.
* The warehouse is implemented using SQLite, making it suitable for educational purposes but not intended for large-scale production deployments.
* Customer churn is defined using a fixed 90-day inactivity threshold, which may not generalize across different businesses or industries.


# 🔮 Future Scope

* Recommendation System using Deep Learning
* Real-time Streaming ETL Pipeline
* Graph-based Customer Analytics
* Advanced Customer Lifetime Value Forecasting
* Reinforcement Learning for Personalized Marketing
* Interactive Dashboard Deployment

---

# ⚡ Installation

```bash
git clone https://github.com/yourusername/customer-segmentation-ecommerce-mining.git

cd customer-segmentation-ecommerce-mining

pip install -r requirements.txt
```

Run the notebooks:

```bash
jupyter notebook
```

---

# 📷 Outputs

The project generates:

* Correlation Heatmaps
* OLAP Dashboards
* Revenue Time-Series Analysis
* Cohort Retention Heatmaps
* PCA & t-SNE Cluster Visualizations
* Dendrograms
* DBSCAN Results
* GMM Analysis
* Churn Prediction Metrics
* SHAP Explainability Plots

---

# 👨‍💻 Authors
**Chaitanya Kashyap** – B240006AI
**Aditya** – B240030CS
4th Semester Project of Data Warehouseing and Mining
Department of Computer Science & Engineering
**National Institute of Technology Sikkim**

---

# 📜 License

This project is intended for **academic and educational purposes**. Feel free to fork and extend it with proper attribution.

---

## ⭐ If you found this project useful, consider giving it a star on GitHub!
