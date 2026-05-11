# 🛒 E-Commerce Customer Analytics Dashboard

An end-to-end customer analytics project on Indian e-commerce order data, covering data cleaning, RFM segmentation, cohort retention analysis, CLV modeling, churn analysis, and an interactive Power BI dashboard.

---

## 📌 Project Overview

This project analyzes e-commerce customer behavior using a full analytics pipeline built in Python. The dataset is modeled on Indian e-commerce context (Flipkart / Amazon India style) — with payment methods like UPI, COD, EMI and categories like Electronics, Fashion, and Grocery. All outputs feed into a multi-page Power BI dashboard.

---

## 🗂️ Project Structure

```
ecommerce-analytics-dashboard/
│
├── python/
│   ├── clean.py      # Data cleaning & Indian context mapping
│   ├── rfm.py        # RFM segmentation — 5 customer segments
│   ├── cohort.py     # Cohort retention matrix (monthly)
│   ├── clv.py        # Customer Lifetime Value — 4 CLV tiers
│   └── churn.py      # Churn analysis — 90-day threshold, risk buckets
│
├── data/
│   ├── ecommerce_cleaned_v2.csv      # Master cleaned dataset
│   ├── rfm_customers.csv             # RFM scores per customer
│   ├── rfm_segments_summary.csv      # Segment-level summary
│   ├── cohort_raw.csv                # Raw cohort data (MySQL)
│   ├── cohort_retention_matrix.csv   # Month-on-month retention matrix
│   ├── cohort_sizes.csv              # New buyers per cohort month
│   ├── clv_customers.csv             # Predicted & historical CLV per customer
│   ├── clv_tier_summary.csv          # Bronze / Silver / Gold / Platinum tiers
│   ├── clv_by_channel.csv            # CLV breakdown by acquisition channel
│   ├── customer_churn.csv            # Churn labels + risk scores per customer
│   ├── churn_risk_summary.csv        # Risk bucket distribution
│   └── churn_by_channel.csv          # Churn rate by marketing channel
│
└── ecommerceproject.pbix             # Power BI Dashboard file
```

---

## 🔧 Tech Stack

| Tool | Usage |
|------|-------|
| Python (Pandas, NumPy) | Data cleaning, RFM, Cohort, CLV, Churn analysis |
| Power BI | Interactive multi-page dashboard |

---

## 📊 Analysis Modules

### 1. Data Cleaning (`clean.py`)
- Dropped irrelevant columns: `location`, `revenue_normalized`, `review_text`, `session_id`
- Decoded encoded columns into human-readable labels using Indian e-commerce context:
  - `payment_method` → UPI, Credit Card, COD, EMI, Net Banking, Debit Card
  - `product_category` → Electronics, Fashion, Home & Kitchen, Grocery, etc.
  - `marketing_channel` → Organic Search, Paid Ads, Social Media, Email, Referral, Direct
  - `device_type` → Mobile, Desktop, Tablet
- Engineered derived columns: `visit_year`, `visit_quarter`, `month_name`
- Result: Zero nulls, fully labeled, analysis-ready dataset

### 2. RFM Segmentation (`rfm.py`)
- Filtered to purchased sessions only
- Scored each customer 1–5 on Recency (lower days = higher score), Frequency, and Monetary value
- Assigned 5 business segments:
  - **Champions** — R≥4, F≥4 (recent + frequent buyers)
  - **Loyal** — R≥3, F≥3 (consistent buyers)
  - **New & Promising** — R≥3, F≤2 (recent but low frequency)
  - **At Risk** — R=2 (going inactive)
  - **Lost** — R=1 (long inactive)
- Output: per-customer RFM scores + segment revenue share summary

### 3. Cohort Retention Analysis (`cohort.py`)
- Assigned each customer a cohort month based on their first-ever purchase
- Calculated month index (Month 0 = acquisition, Month 1 = one month later, etc.)
- Built a retention matrix showing what % of each cohort returns each month
- Identified best and worst performing cohorts by Month-1 retention rate

### 4. CLV Modeling (`clv.py`)
- Computed per-customer: lifespan (days), monthly purchase frequency, avg order value
- Projected 12-month predicted CLV: `avg_order_value × purchase_freq_monthly × 12`
- Segmented customers into 4 CLV tiers: Bronze, Silver, Gold, Platinum
- Broke down CLV by marketing channel and device type to identify highest-value acquisition sources

### 5. Churn Analysis (`churn.py`)
- Defined churn threshold: 90 days of inactivity = churned
- Segmented active customers into churn risk buckets:
  - **Low Risk** — purchased within last 30 days
  - **Medium Risk** — 31–60 days inactive
  - **High Risk** — 61–90 days inactive (about to churn)
- Analyzed churn rate by marketing channel, device type, and product category
- Calculated revenue at risk from churned customers

---

## 💡 Key Insights

- **Champions segment** drives a disproportionate share of total revenue despite being a small % of customers
- **Cohort retention** drops significantly after Month 1 — Month 2+ retention is the key business problem
- **Email Campaign** channel produces the highest predicted CLV customers
- **COD customers** show the highest churn rate; UPI customers are most retained
- **High Risk** bucket (61–90 days inactive) represents the most actionable re-engagement target

---

## ▶️ How to Run

Run scripts in this order:

```bash
python clean.py    # Generates ecommerce_cleaned_v2.csv
python rfm.py      # Generates rfm_customers.csv, rfm_segments_summary.csv
python cohort.py   # Generates cohort_retention_matrix.csv, cohort_raw.csv, cohort_sizes.csv
python clv.py      # Generates clv_customers.csv, clv_tier_summary.csv, clv_by_channel.csv
python churn.py    # Generates customer_churn.csv, churn_risk_summary.csv, churn_by_channel.csv
```

Then open `ecommerceproject.pbix` in Power BI Desktop and refresh data source connections.

---

## 📦 Data Source

- E-commerce sessions dataset sourced from Kaggle
- Decoded and mapped to Indian e-commerce context (UPI payments, Indian product categories, regional marketing channels)
