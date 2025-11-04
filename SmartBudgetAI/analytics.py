# analytics.py
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression

def to_datetime(df, date_col="date"):
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    return df

def monthly_category_totals(df):
    df = to_datetime(df)
    df['year_month'] = df['date'].dt.to_period('M').astype(str)
    return df.groupby(['category','year_month'])['amount'].sum().reset_index()

def detect_high_single_expenses(df, threshold=60):
    # returns rows with amount > threshold
    if df is None or df.empty:
        return df
    return df[df['amount'] > threshold].sort_values('date', ascending=False)

def biweekly_summary(df, ref_date=None):
    if df is None or df.empty:
        return pd.DataFrame(), 0.0, 0.0
    if ref_date is None:
        ref_date = datetime.today()
    df = to_datetime(df)
    end = pd.Timestamp(ref_date).normalize()
    start = end - pd.Timedelta(days=13)  # include today: last 14 days
    last_period = df[(df['date'] >= start) & (df['date'] <= end)]
    prev_start = start - pd.Timedelta(days=14)
    prev_end = start - pd.Timedelta(days=1)
    prev_period = df[(df['date'] >= prev_start) & (df['date'] <= prev_end)]
    last_sum = last_period.groupby('category')['amount'].sum()
    prev_sum = prev_period.groupby('category')['amount'].sum()
    pct = ((last_sum - prev_sum) / (prev_sum.replace(0, np.nan))) * 100
    pct = pct.fillna(0)
    summary = pd.DataFrame({
        'category': last_sum.index,
        'last_14_sum': last_sum.values,
        'prev_14_sum': [prev_sum.get(c, 0.0) for c in last_sum.index],
        'pct_change': [pct.get(c, 0.0) for c in last_sum.index]
    })
    total_last = float(last_period['amount'].sum())
    total_prev = float(prev_period['amount'].sum())
    return summary, total_last, total_prev

def simple_category_prediction(df, target_category):
    if df is None or df.empty:
        return None
    mdf = monthly_category_totals(df)
    cat = mdf[mdf['category'] == target_category].copy()
    if cat.empty or len(cat) < 2:
        return None
    cat['year_month'] = pd.to_datetime(cat['year_month'].astype(str) + '-01')
    cat = cat.sort_values('year_month')
    cat['t'] = (cat['year_month'] - cat['year_month'].min()).dt.days
    X = cat[['t']].values
    y = cat['amount'].values
    model = LinearRegression().fit(X, y)
    next_t = (cat['year_month'].max() + pd.offsets.MonthBegin(1) - cat['year_month'].min()).days
    pred = model.predict([[next_t]])
    return float(max(pred[0], 0.0))
