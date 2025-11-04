# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date as dt_date
from db import add_expense, get_expenses
from analytics import detect_high_single_expenses, biweekly_summary, simple_category_prediction


st.title("💰 SmartBudget AI")
st.subheader("Track Your Coin Moves & Watch Your Money Grow")

# Input form
st.header("Add Your Expense")
with st.form("expense_form"):
    d = st.date_input("Date", value=dt_date.today())
    category = st.selectbox("Category", ["Food", "Rent", "Travel", "Shopping", "Other"])
    amount = st.number_input("Amount ($)", min_value=0.0, step=0.5)
    note = st.text_input("Note (optional)")
    submitted = st.form_submit_button("Add Expense")

if submitted:
    # save to DB
    add_expense(d.isoformat(), category, amount, note)
    st.success(" Expense added to DB")

# Load and show expenses from DB
df = get_expenses()
st.subheader("Your Expenses")
if df.empty:
    st.write("No expenses yet. Add one above.")
else:
    # convert date column to datetime for friendly display and sorting
    df['date'] = pd.to_datetime(df['date'])
    st.dataframe(df[['date', 'category', 'amount', 'note']])

# Visualization
if not df.empty:
    st.subheader("Spending by Category (all time)")
    fig, ax = plt.subplots()
    df.groupby("category")["amount"].sum().plot(kind="bar", ax=ax)
    ax.set_ylabel("Amount ($)")
    st.pyplot(fig)

st.markdown("### Alerts")
threshold = st.slider("Highlight single expenses above (USD)", 10, 500, 60)
highs = detect_high_single_expenses(df, threshold)
if highs is None or highs.empty:
    st.write("No high single-item expenses found.")
else:
    st.write("High single-item expenses:")
    st.table(highs[['date','item']].assign(Category=highs.get('category', highs.get('Category', ''))).rename(columns={'item':'Item'}).head(10))


st.markdown("### Biweekly Summary (manual)")
if st.button("Generate Biweekly Summary"):
    summary, total_last, total_prev = biweekly_summary(df)
    st.write(f"Total last 14 days: ${total_last:.2f}  —  previous 14 days: ${total_prev:.2f}")
    if summary.empty:
        st.write("No data for the last 28 days.")
    else:
        st.dataframe(summary)
        anomalies = summary[summary['pct_change'].abs() >= 50]
        if not anomalies.empty:
            st.warning("Categories with large % change:")
            st.table(anomalies)

st.markdown("### Predict next month spending for a category")
if not df.empty:
    cat_choice = st.selectbox("Pick category", options=sorted(df['category'].unique()))
else:
    cat_choice = st.text_input("Category (no data yet)", value="Food")
if st.button("Predict next month"):
    pred = simple_category_prediction(df, cat_choice)
    if pred is None:
        st.info("Not enough historical monthly data to make prediction.")
    else:
        st.success(f"Predicted spend for next month in {cat_choice}: ${pred:.2f}")

# CSV download
csv = df.to_csv(index=False)
st.download_button("Download expenses CSV", data=csv, file_name="expenses.csv", mime="text/csv")
