import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient

def render_dashboard(user_id):
    st.title("📊 Your Financial Dashboard")

    # --- MongoDB Connection ---
    client = MongoClient(st.secrets["MONGO_URI"])
    db = client["finance_ai"]
    transactions_collection = db["transactions"]
    user_profiles_collection = db["user_profiles"]
    
    # --- Load Financial Summary ---
    financial = user_profiles_collection.find_one({"user_id": user_id})
    if not financial:
        st.warning("No financial summary found for this user.")
        return
    
    st.subheader("📌 Current Financial Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Cash Holdings", f"₹ {financial['cash_holdings']:.2f}")
    col2.metric("🏦 Online Holdings", f"₹ {financial['online_holdings']:.2f}")
    col3.metric("📈 Stock Investments", f"₹ {financial['stock_investments']:.2f}")

    col4, col5 = st.columns(2)
    col4.metric("📈 Savings", f"₹ {financial['savings']:.2f}")
    col5.metric("💾 Total Savings", f"₹ {financial['total_savings']:.2f}")

    st.markdown("---")

    # --- Editable Section ---
    st.subheader("🔧 Update Your Holdings")

    with st.form("update_holdings_form"):
        cash_change = st.number_input("Change in Cash Holdings (₹)", value=0.0, format="%.2f")
        online_change = st.number_input("Change in Online Holdings (₹)", value=0.0, format="%.2f")
        stock_change = st.number_input("Change in Stock Investments (₹)", value=0.0, format="%.2f")
        savings_change = st.number_input("Change in Savings (₹)", value=0.0, format="%.2f")
        submitted = st.form_submit_button("Update Holdings")

        if submitted:
            updated_values = {
                "cash_holdings": financial["cash_holdings"] + cash_change,
                "online_holdings": financial["online_holdings"] + online_change,
                "stock_investments": financial["stock_investments"] + stock_change,
                "savings": financial["savings"] + savings_change
            }
            updated_values["total_savings"] = (
                updated_values["stock_investments"] +
                updated_values["savings"]
            )

            # Update MongoDB
            user_profiles_collection.update_one(
                {"user_id": user_id},
                {"$set": updated_values}
            )
            st.success("✅ Holdings updated successfully!")
            st.rerun()

    st.markdown("---")

    # --- Fetch User's Transactions ---
    transactions = list(transactions_collection.find({"user_id": user_id}))

    if not transactions:
        st.warning("No transactions found for this user.")
        return

    # --- Preprocessing ---
    df = pd.DataFrame(transactions)
    df["amount"] = df["amount"].astype(float)
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    df["category"] = df["category"].str.title()

    income_df = df[df["amount_type"] == "credit"]
    expense_df = df[df["amount_type"] == "debit"]

    # --- Metrics ---
    total_income = income_df["amount"].sum()
    total_expense = expense_df["amount"].sum()
    net_savings = total_income - total_expense

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Income", f"₹{total_income:,.2f}")
    col2.metric("🧾 Total Expenses", f"₹{total_expense:,.2f}")
    col3.metric("🏦 Net Savings", f"₹{net_savings:,.2f}")

    st.markdown("---")

    # --- Bar Chart: Category-wise Expenses ---
    st.subheader("📂 Expenses by Category")
    category_expense = expense_df.groupby("category")["amount"].sum().sort_values(ascending=False)
    fig1 = px.bar(
        category_expense,
        x=category_expense.index,
        y=category_expense.values,
        labels={"x": "Category", "y": "Total Spent"},
        title="Expenses by Category",
        color=category_expense.values,
        color_continuous_scale="reds"
    )
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("---")

    # --- Timeline Chart: Income vs Expenses Over Time ---
    st.subheader("📅 Income vs Expenses Over Time")

    # Group income and expense by date
    income_by_date = income_df.groupby("transaction_date")["amount"].sum().rename("credit")
    expense_by_date = expense_df.groupby("transaction_date")["amount"].sum().rename("debit")

    # Merge them on date
    timeline_df = pd.concat([income_by_date, expense_by_date], axis=1).fillna(0).reset_index()

    # Melt for Plotly
    timeline_df_melted = timeline_df.melt(
        id_vars="transaction_date",
        value_vars=["credit", "debit"],
        var_name="Transaction Type",
        value_name="Amount"
    )

    # Line chart
    fig2 = px.line(
        timeline_df_melted,
        x="transaction_date",
        y="Amount",
        color="Transaction Type",
        labels={"transaction_date": "Date"},
        title="📅 Income vs Expenses Over Time"
    )
    st.plotly_chart(fig2, use_container_width=True)