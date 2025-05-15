import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime

def debts_page(user_id):
    st.title("Debt & Loan Tracker")

    # MongoDB connection
    client = MongoClient(st.secrets["MONGO_URI"])
    db = client["finance_ai"]
    debts_collection = db["debts"]

    # --- Add New Debt ---
    st.subheader("Add a New Debt or Loan")

    with st.form("add_debt_form"):
        name = st.text_input("Debt/Loan Name", placeholder="e.g., Car Loan")
        amount = st.number_input("Loan Amount (₹)", min_value=0.0, step=100.0, format="%.2f")
        interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, step=0.1, format="%.2f")
        priority = st.selectbox("Priority", options=["High", "Medium", "Low"])
        submitted = st.form_submit_button("Add Debt")

        if submitted:
            if not name:
                st.warning("Please enter a name for the debt.")
            else:
                debt_doc = {
                    "user_id": user_id,
                    "name": name.strip(),
                    "amount": amount,
                    "interest_rate": interest_rate,
                    "priority": priority,
                    "created_at": datetime.now()
                }
                debts_collection.insert_one(debt_doc)
                st.success(f"Added '{name}' to your debt records!")

    # --- View Existing Debts ---
    st.subheader("Your Existing Debts & Loans")
    debts = list(debts_collection.find({"user_id": user_id}))
    if debts:
        debt_df = pd.DataFrame(debts)
        debt_df.drop(columns=["_id", "user_id"], inplace=True, errors="ignore")
        debt_df = debt_df.rename(columns={
            "name": "Debt Name",
            "amount": "Amount (₹)",
            "interest_rate": "Interest Rate (%)",
            "priority": "Priority",
            "created_at": "Created At"
        })
        st.dataframe(debt_df)
    else:
        st.info("You have not recorded any debts or loans yet.")

    client.close()