
import pandas as pd
import numpy as np

# ── STEP 1: LOAD CLEANED DATA ─────────────────────────────
# Change filename below if you saved with a different name

df = pd.read_csv('F:\CODING\ecommerce_cleaned_v2.csv')
df['visit_date'] = pd.to_datetime(df['visit_date'], dayfirst=True)

print("=" * 55)
print("DATASET OVERVIEW")
print("=" * 55)
print(f"Total rows       : {len(df):,}")
print(f"Unique customers : {df['customer_id'].nunique():,}")
print(f"Date range       : {df['visit_date'].min().date()} to {df['visit_date'].max().date()}")
print()

# ── STEP 2: FILTER — PURCHASED SESSIONS ONLY ──────────────
# RFM only makes sense for customers who actually purchased
# Non-purchase visits (revenue=0) are excluded

purchased = df[df['purchased'] == 'Purchased'].copy()

print(f"Purchased sessions   : {len(purchased):,}")
print(f"Non-purchased visits : {len(df) - len(purchased):,}")
print(f"Customers who bought : {purchased['customer_id'].nunique():,}")
print()

# ── STEP 3: SNAPSHOT DATE ─────────────────────────────────
# Reference point for Recency calculation
# Convention: last date in dataset + 1 day

snapshot_date = purchased['visit_date'].max() + pd.Timedelta(days=1)
print(f"Snapshot date : {snapshot_date.date()}")
print()

# ── STEP 4: CALCULATE R, F, M PER CUSTOMER ────────────────

rfm = purchased.groupby('customer_id').agg(
    last_purchase_date = ('visit_date', 'max'),
    frequency          = ('visit_date', 'count'),
    monetary           = ('revenue', 'sum')
).reset_index()

# Recency = days since last purchase (lower = better)
rfm['recency'] = (snapshot_date - rfm['last_purchase_date']).dt.days
rfm = rfm.drop(columns=['last_purchase_date'])

print("=" * 55)
print("RFM BASE TABLE — Sample")
print("=" * 55)
print(rfm.head())
print()
print("RFM Stats:")
print(rfm[['recency', 'frequency', 'monetary']].describe().round(2))
print()

# ── STEP 5: SCORING 1 TO 5 ────────────────────────────────
# Recency  -> lower days = better -> reverse scored (5=best)
# Frequency -> higher = better -> 5=best
# Monetary  -> higher = better -> 5=best

rfm['r_score'] = pd.qcut(
    rfm['recency'], q=5, labels=[5, 4, 3, 2, 1]
).astype(int)

rfm['f_score'] = pd.qcut(
    rfm['frequency'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5]
).astype(int)

rfm['m_score'] = pd.qcut(
    rfm['monetary'], q=5, labels=[1, 2, 3, 4, 5]
).astype(int)

# Combined score string e.g. "555" = best customer
rfm['rfm_score'] = (rfm['r_score'].astype(str)
                  + rfm['f_score'].astype(str)
                  + rfm['m_score'].astype(str))

# Numeric total for sorting
rfm['rfm_total'] = rfm['r_score'] + rfm['f_score'] + rfm['m_score']

# ── STEP 6: SEGMENT ASSIGNMENT (5 clean segments) ─────────

def assign_segment(row):
    r = row['r_score']
    f = row['f_score']

    if r >= 4 and f >= 4:
        return 'Champions'          # Recent + frequent buyers
    elif r >= 3 and f >= 3:
        return 'Loyal'              # Consistent buyers
    elif r >= 3 and f <= 2:
        return 'New & Promising'    # Recent but low frequency
    elif r == 2:
        return 'At Risk'            # Starting to go inactive
    else:                           # r == 1
        return 'Lost'               # Long inactive

rfm['segment'] = rfm.apply(assign_segment, axis=1)

# ── STEP 7: SEGMENT SUMMARY ───────────────────────────────

segment_summary = rfm.groupby('segment').agg(
    customer_count = ('customer_id', 'count'),
    avg_recency    = ('recency', 'mean'),
    avg_frequency  = ('frequency', 'mean'),
    avg_monetary   = ('monetary', 'mean'),
    total_revenue  = ('monetary', 'sum')
).round(2).sort_values('customer_count', ascending=False)

segment_summary['revenue_share_%'] = (
    segment_summary['total_revenue'] /
    segment_summary['total_revenue'].sum() * 100
).round(2)

print("=" * 55)
print("SEGMENT DISTRIBUTION")
print("=" * 55)
print(segment_summary.to_string())
print()

# ── STEP 8: SAVE ──────────────────────────────────────────

rfm.to_csv('rfm_customers.csv', index=False)
segment_summary.reset_index().to_csv('rfm_segments_summary.csv', index=False)

print("=" * 55)
print("FILES SAVED")
print("=" * 55)
print("rfm_customers.csv        -> Full RFM per customer (MySQL)")
print("rfm_segments_summary.csv -> Segment summary (Power BI)")
print()
