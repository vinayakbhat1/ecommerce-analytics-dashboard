

import pandas as pd

# ── STEP 1: LOAD & FILTER ──────────────────────────────────

df = pd.read_csv('F:\CODING\ecommerce_cleaned_v2.csv')
df['visit_date'] = pd.to_datetime(df['visit_date'], dayfirst=True)

# Only purchased sessions matter for cohort
purchased = df[df['purchased'] == 'Purchased'].copy()

print("=" * 55)
print("COHORT ANALYSIS — E-Commerce Dataset")
print("=" * 55)
print(f"Purchased sessions  : {len(purchased):,}")
print(f"Unique buyers       : {purchased['customer_id'].nunique():,}")
print()

# ── STEP 2: ASSIGN COHORT MONTH ───────────────────────────
# Cohort = month of customer's FIRST ever purchase

purchased['order_month'] = purchased['visit_date'].dt.to_period('M')

cohort_map = (
    purchased.groupby('customer_id')['order_month']
    .min()
    .reset_index()
    .rename(columns={'order_month': 'cohort_month'})
)

purchased = purchased.merge(cohort_map, on='customer_id', how='left')

# ── STEP 3: CALCULATE MONTH INDEX ─────────────────────────
# Month 0 = first purchase month (always 100%)
# Month 1 = one month later, etc.

purchased['month_index'] = (
    purchased['order_month'] - purchased['cohort_month']
).apply(lambda x: x.n)

# ── STEP 4: BUILD COHORT PIVOT TABLE ──────────────────────

cohort_data = (
    purchased.groupby(['cohort_month', 'month_index'])['customer_id']
    .nunique()
    .reset_index()
    .rename(columns={'customer_id': 'customer_count'})
)

cohort_pivot = cohort_data.pivot_table(
    index='cohort_month',
    columns='month_index',
    values='customer_count'
)

# ── STEP 5: RETENTION RATE MATRIX ─────────────────────────

cohort_size     = cohort_pivot[0]
retention_matrix = cohort_pivot.divide(cohort_size, axis=0).round(4) * 100

print("=" * 55)
print("COHORT SIZE (new buyers per month)")
print("=" * 55)
print(cohort_size.to_string())
print()

print("=" * 55)
print("RETENTION MATRIX (%)")
print("=" * 55)
retention_display = retention_matrix.map(
    lambda x: f"{x:.1f}%" if not pd.isna(x) else "-"
)
print(retention_display.to_string())
print()

# ── STEP 6: KEY INSIGHTS ──────────────────────────────────

print("=" * 55)
print("KEY INSIGHTS")
print("=" * 55)

m1 = retention_matrix[1].dropna()
print(f"Avg Month-1 Retention  : {m1.mean():.1f}%")
print(f"Best Cohort  (Month-1) : {m1.idxmax()} -> {m1.max():.1f}%")
print(f"Worst Cohort (Month-1) : {m1.idxmin()} -> {m1.min():.1f}%")
print()

print("Avg Retention by Month:")
for month, rate in retention_matrix.mean().dropna().items():
    bar = "█" * int(rate / 5)
    print(f"  Month {month:>2} : {rate:>5.1f}%  {bar}")
print()

# ── STEP 7: SAVE ──────────────────────────────────────────

# For Power BI heatmap
retention_matrix.reset_index().to_csv('cohort_retention_matrix.csv', index=False)

# For MySQL import
cohort_data['cohort_month'] = cohort_data['cohort_month'].astype(str)
cohort_data.to_csv('cohort_raw.csv', index=False)

# Cohort sizes reference
cohort_size_df = cohort_size.reset_index()
cohort_size_df.columns = ['cohort_month', 'cohort_size']
cohort_size_df['cohort_month'] = cohort_size_df['cohort_month'].astype(str)
cohort_size_df.to_csv('cohort_sizes.csv', index=False)

print("=" * 55)
print("FILES SAVED")
print("=" * 55)
print("cohort_retention_matrix.csv -> Power BI heatmap")
print("cohort_raw.csv              -> MySQL import")
print("cohort_sizes.csv            -> Cohort size reference")

