import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import pandas as pd

# ------------------ MongoDB Utilities ------------------
def add_transaction(transactions):
    client = MongoClient('mongodb://localhost:27017/')
    db = client['finance_ai']
    collection = db['transactions']
    collection.insert_one(transactions)
    client.close()

def get_transactions(user_id):
    client = MongoClient('mongodb://localhost:27017/')
    db = client['finance_ai']
    collection = db['transactions']
    transactions = list(collection.find({"user_id": user_id}))
    client.close()
    return transactions

def auto_add_subscriptions(user_id):
    client = MongoClient("mongodb://localhost:27017/")
    db = client['finance_ai']
    subscriptions = db['subscriptions']
    transactions = db['transactions']

    today = datetime.utcnow()
    start_date = datetime(today.year, today.month, 1)

    # Get first day of next month
    if today.month == 12:
        end_date = datetime(today.year + 1, 1, 1)
    else:
        end_date = datetime(today.year, today.month + 1, 1)

    subs = list(subscriptions.find({"user_id": user_id}))

    for sub in subs:
        sub_name = sub['name']
        sub_cost = sub['cost']

        existing_expense = transactions.find_one({
            "user_id": user_id,
            "description": f"Subscription: {sub_name}",
            "amount_type": "expense",
            "transaction_date": {
                "$gte": start_date,
                "$lt": end_date
            }
        })

        if not existing_expense:
            new_expense = {
                "user_id": user_id,
                "amount": sub_cost,
                "amount_type": "expense",
                "category": "Subscription",
                "description": f"Subscription: {sub_name}",
                "transaction_date": today
            }
            transactions.insert_one(new_expense)

    client.close()

# ------------------ Main Page ------------------
def home_page(user_id):
    # st.set_page_config(page_title="Finance Tracker", layout="centered")
    st.title("💰 Personal Finance Tracker")

    with st.expander("➕ Add New Transaction", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("📅 Date", value=datetime.today())
            category = st.selectbox("📂 Category", ["Food", "Travel", "Rent", "Salary", "Shopping", "Healthcare", "Utilities", "Miscellaneous"])
        with col2:
            amount = st.number_input("💸 Amount", min_value=0.0, format="%.2f")
            amount_type = st.radio("📈 Type", ["Income", "Expense"], horizontal=True)
        
        description = st.text_input("📝 Description")

        if st.button("✅ Add Transaction"):
            transaction = {
                "user_id": user_id,
                "transaction_date": date.strftime("%Y-%m-%d"),
                "amount": amount,
                "amount_type": "credit" if amount_type == "Income" else "debit",
                "category": category,
                "description": description
            }
            add_transaction(transaction)
            st.success("🎉 Transaction added successfully!")

    # ------------------ Transaction History ------------------
    st.subheader("📊 Transaction History")

    transactions = get_transactions(user_id)
    
    auto_add_subscriptions(user_id)

    if transactions:
        # Convert to DataFrame for formatting
        df = pd.DataFrame(transactions)
        df = df.drop(columns=["_id", "user_id"])

        df["transaction_date"] = pd.to_datetime(df["transaction_date"]).dt.strftime("%b %d, %Y")

        # Color styling
        def highlight_type(val):
            color = "lightgreen" if val == "debit" else "salmon"
            return f"background-color: {color}"

        st.dataframe(
            df.style.applymap(highlight_type, subset=["amount_type"]),
            use_container_width=True,
            height=400
        )
        
    else:
        st.info("No transactions recorded yet. Add your first transaction above! 🚀")