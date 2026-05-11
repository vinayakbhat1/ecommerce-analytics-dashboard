import pandas as pd
import numpy as np

# ── STEP 1: LOAD DATA ──────────────────────────────────────

df = pd.read_csv('F:\CODING\ecommerce_cleaned_v2.csv')
df['visit_date'] = pd.to_datetime(df['visit_date'])

purchased = df[df['purchased'] == 'Purchased'].copy()

snapshot_date = purchased['visit_date'].max() + pd.Timedelta(days=1)

print("=" * 55)
print("CLV ANALYSIS — E-Commerce Dataset")
print("=" * 55)
print(f"Snapshot date    : {snapshot_date.date()}")
print(f"Buying customers : {purchased['customer_id'].nunique():,}")
print()

# ── STEP 2: PER CUSTOMER METRICS ──────────────────────────

clv_df = purchased.groupby('customer_id').agg(
    first_purchase = ('visit_date', 'min'),
    last_purchase  = ('visit_date', 'max'),
    total_orders   = ('visit_date', 'count'),
    total_revenue  = ('revenue', 'sum'),
    avg_order_value= ('revenue', 'mean'),
    product_category = ('product_category', lambda x: x.mode()[0]),
    device_type    = ('device_type', lambda x: x.mode()[0]),
    marketing_channel = ('marketing_channel', lambda x: x.mode()[0]),
).reset_index()

# ── STEP 3: CALCULATE CLV COMPONENTS ──────────────────────

# Customer lifespan in days (first to last purchase)
# Minimum 1 day to avoid division by zero for single purchasers
clv_df['lifespan_days'] = (
    clv_df['last_purchase'] - clv_df['first_purchase']
).dt.days.clip(lower=1)

# Lifespan in months
clv_df['lifespan_months'] = (clv_df['lifespan_days'] / 30).round(2)

# Purchase frequency per month
# For single purchase customers → 1 purchase over lifespan
clv_df['purchase_freq_monthly'] = (
    clv_df['total_orders'] / clv_df['lifespan_months']
).round(4)

# Cap frequency at reasonable max (handles single purchasers
# who have lifespan of 1 day but 1 purchase = very high rate)
clv_df['purchase_freq_monthly'] = clv_df['purchase_freq_monthly'].clip(upper=5)

# ── STEP 4: PROJECT FORWARD 12 MONTHS ─────────────────────
# Predicted CLV for next 12 months based on historical behavior

projection_months = 12

clv_df['predicted_clv'] = (
    clv_df['avg_order_value'] *
    clv_df['purchase_freq_monthly'] *
    projection_months
).round(2)

# Historical CLV = actual revenue generated so far
clv_df['historical_clv'] = clv_df['total_revenue'].round(2)

print("=" * 55)
print("CLV STATS")
print("=" * 55)
print(clv_df[['avg_order_value', 'purchase_freq_monthly',
              'historical_clv', 'predicted_clv']].describe().round(2))
print()

# ── STEP 5: CLV TIER SEGMENTATION ─────────────────────────
# Segment customers into 4 tiers based on predicted CLV

clv_df['clv_tier'] = pd.qcut(
    clv_df['predicted_clv'],
    q=4,
    labels=['Bronze', 'Silver', 'Gold', 'Platinum']
)

# ── STEP 6: TIER SUMMARY ──────────────────────────────────

tier_summary = clv_df.groupby('clv_tier', observed=True).agg(
    customer_count    = ('customer_id', 'count'),
    avg_predicted_clv = ('predicted_clv', 'mean'),
    avg_historical_clv= ('historical_clv', 'mean'),
    avg_order_value   = ('avg_order_value', 'mean'),
    avg_orders        = ('total_orders', 'mean'),
    total_predicted   = ('predicted_clv', 'sum')
).round(2)

tier_summary['revenue_share_%'] = (
    tier_summary['total_predicted'] /
    tier_summary['total_predicted'].sum() * 100
).round(2)

print("=" * 55)
print("CLV TIER DISTRIBUTION")
print("=" * 55)
print(tier_summary.to_string())
print()

# ── STEP 7: CLV BY MARKETING CHANNEL ──────────────────────

print("=" * 55)
print("AVG CLV BY MARKETING CHANNEL")
print("=" * 55)

channel_clv = clv_df.groupby('marketing_channel').agg(
    customer_count    = ('customer_id', 'count'),
    avg_predicted_clv = ('predicted_clv', 'mean'),
    avg_order_value   = ('avg_order_value', 'mean')
).round(2).sort_values('avg_predicted_clv', ascending=False)

print(channel_clv.to_string())
print()

# ── STEP 8: CLV BY DEVICE TYPE ────────────────────────────

print("=" * 55)
print("AVG CLV BY DEVICE TYPE")
print("=" * 55)

device_clv = clv_df.groupby('device_type').agg(
    customer_count    = ('customer_id', 'count'),
    avg_predicted_clv = ('predicted_clv', 'mean'),
    avg_order_value   = ('avg_order_value', 'mean')
).round(2).sort_values('avg_predicted_clv', ascending=False)

print(device_clv.to_string())
print()

# ── STEP 9: TOP 10 HIGHEST CLV CUSTOMERS ──────────────────

print("=" * 55)
print("TOP 10 CUSTOMERS BY PREDICTED CLV")
print("=" * 55)

top10 = clv_df.nlargest(10, 'predicted_clv')[
    ['customer_id', 'total_orders', 'avg_order_value',
     'predicted_clv', 'historical_clv', 'clv_tier']
]
print(top10.to_string(index=False))
print()

# ── STEP 10: SAVE ─────────────────────────────────────────

# Drop date columns before saving
save_df = clv_df.drop(columns=['first_purchase', 'last_purchase'])
save_df['clv_tier'] = save_df['clv_tier'].astype(str)
save_df.to_csv('clv_customers.csv', index=False)

tier_summary.reset_index().to_csv('clv_tier_summary.csv', index=False)
channel_clv.reset_index().to_csv('clv_by_channel.csv', index=False)

print("=" * 55)
print("FILES SAVED")
print("=" * 55)
print("clv_customers.csv    -> Full CLV per customer (MySQL)")
print("clv_tier_summary.csv -> Tier summary (Power BI)")
print("clv_by_channel.csv   -> Channel CLV (Power BI)")
print()

print("CLV ANALYSIS COMPLETE")
