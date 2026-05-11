import pandas as pd

# ── STEP 1: LOAD DATA ──────────────────────────────────────

df = pd.read_csv('F:\CODING\ecommerce_cleaned_v2.csv')
df['visit_date'] = pd.to_datetime(df['visit_date'])

purchased = df[df['purchased'] == 'Purchased'].copy()

snapshot_date  = purchased['visit_date'].max() + pd.Timedelta(days=1)
churn_threshold = 90  # days

print("=" * 55)
print("CHURN ANALYSIS — E-Commerce Dataset")
print("=" * 55)
print(f"Snapshot date    : {snapshot_date.date()}")
print(f"Churn threshold  : {churn_threshold} days")
print(f"Churn cutoff     : customers last seen before "
      f"{(snapshot_date - pd.Timedelta(days=churn_threshold)).date()}")
print()

# ── STEP 2: LAST PURCHASE DATE PER CUSTOMER ───────────────

customer_last = (
    purchased.groupby('customer_id')
    .agg(
        last_purchase_date = ('visit_date', 'max'),
        total_purchases    = ('visit_date', 'count'),
        total_revenue      = ('revenue', 'sum'),
        avg_order_value    = ('revenue', 'mean'),
        product_category   = ('product_category', lambda x: x.mode()[0]),
        device_type        = ('device_type', lambda x: x.mode()[0]),
        payment_method     = ('payment_method', lambda x: x.mode()[0]),
        marketing_channel  = ('marketing_channel', lambda x: x.mode()[0]),
    )
    .reset_index()
)

# Days since last purchase
customer_last['days_since_purchase'] = (
    snapshot_date - customer_last['last_purchase_date']
).dt.days

# ── STEP 3: ASSIGN CHURN FLAG ─────────────────────────────

customer_last['churn_status'] = customer_last['days_since_purchase'].apply(
    lambda x: 'Churned' if x > churn_threshold else 'Active'
)

# Binary flag for ML / Power BI calculations
customer_last['is_churned'] = (
    customer_last['churn_status'] == 'Churned'
).astype(int)

print("=" * 55)
print("OVERALL CHURN SUMMARY")
print("=" * 55)

total     = len(customer_last)
churned   = customer_last['is_churned'].sum()
active    = total - churned
churn_rate = churned / total * 100

print(f"Total customers  : {total:,}")
print(f"Active customers : {active:,}  ({100 - churn_rate:.1f}%)")
print(f"Churned customers: {churned:,}  ({churn_rate:.1f}%)")
print()

# ── STEP 4: CHURN BY DEVICE TYPE ──────────────────────────

print("=" * 55)
print("CHURN BY DEVICE TYPE")
print("=" * 55)

device_churn = customer_last.groupby('device_type').agg(
    total    = ('customer_id', 'count'),
    churned  = ('is_churned', 'sum')
).reset_index()
device_churn['churn_rate_%'] = (
    device_churn['churned'] / device_churn['total'] * 100
).round(2)
print(device_churn.to_string(index=False))
print()

# ── STEP 5: CHURN BY MARKETING CHANNEL ────────────────────

print("=" * 55)
print("CHURN BY MARKETING CHANNEL")
print("=" * 55)

channel_churn = customer_last.groupby('marketing_channel').agg(
    total    = ('customer_id', 'count'),
    churned  = ('is_churned', 'sum')
).reset_index()
channel_churn['churn_rate_%'] = (
    channel_churn['churned'] / channel_churn['total'] * 100
).round(2)
channel_churn = channel_churn.sort_values('churn_rate_%', ascending=False)
print(channel_churn.to_string(index=False))
print()

# ── STEP 6: CHURN BY PRODUCT CATEGORY ─────────────────────

print("=" * 55)
print("CHURN BY PRODUCT CATEGORY")
print("=" * 55)

cat_churn = customer_last.groupby('product_category').agg(
    total    = ('customer_id', 'count'),
    churned  = ('is_churned', 'sum')
).reset_index()
cat_churn['churn_rate_%'] = (
    cat_churn['churned'] / cat_churn['total'] * 100
).round(2)
cat_churn = cat_churn.sort_values('churn_rate_%', ascending=False)
print(cat_churn.to_string(index=False))
print()

# ── STEP 7: REVENUE LOST TO CHURN ─────────────────────────

print("=" * 55)
print("REVENUE IMPACT")
print("=" * 55)

total_rev   = customer_last['total_revenue'].sum()
churned_rev = customer_last[customer_last['is_churned'] == 1]['total_revenue'].sum()
active_rev  = total_rev - churned_rev

print(f"Total revenue from all customers : Rs. {total_rev:,.2f}")
print(f"Revenue from active customers    : Rs. {active_rev:,.2f}")
print(f"Revenue from churned customers   : Rs. {churned_rev:,.2f}")
print(f"  -> {churned_rev/total_rev*100:.1f}% of total revenue came from now-churned customers")
print()

# ── STEP 8: CHURN RISK BUCKETS ────────────────────────────
# Segment active customers by churn risk
# So business knows WHO to target first

def churn_risk(days):
    if days <= churn_threshold:
        if days <= 30:
            return 'Low Risk'       # purchased in last 30 days
        elif days <= 60:
            return 'Medium Risk'    # 31-60 days
        else:
            return 'High Risk'      # 61-90 days (about to churn)
    else:
        return 'Churned'

customer_last['churn_risk'] = customer_last['days_since_purchase'].apply(churn_risk)

risk_summary = customer_last.groupby('churn_risk').agg(
    customer_count = ('customer_id', 'count'),
    avg_revenue    = ('total_revenue', 'mean'),
    total_revenue  = ('total_revenue', 'sum')
).round(2)
risk_summary['revenue_share_%'] = (
    risk_summary['total_revenue'] /
    risk_summary['total_revenue'].sum() * 100
).round(2)

print("=" * 55)
print("CHURN RISK BUCKETS (Active Customers)")
print("=" * 55)
print(risk_summary.to_string())
print()

# ── STEP 9: SAVE ──────────────────────────────────────────

# Drop date column before saving (not needed in MySQL)
save_df = customer_last.drop(columns=['last_purchase_date'])
save_df.to_csv('customer_churn.csv', index=False)

risk_summary.reset_index().to_csv('churn_risk_summary.csv', index=False)
channel_churn.to_csv('churn_by_channel.csv', index=False)

print("=" * 55)
print("FILES SAVED")
print("=" * 55)
print("customer_churn.csv      -> Full churn table (MySQL)")
print("churn_risk_summary.csv  -> Risk buckets (Power BI)")
print("churn_by_channel.csv    -> Channel churn (Power BI)")
print()
