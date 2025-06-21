import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import pandas as pd
import requests
import base64
import json
from bson import ObjectId
import time
from utils.categories import get_user_categories, add_custom_category

BACKEND_URL = st.secrets["BACKEND_URL"]
LOCAL_URL = st.secrets["LOCAL_URL"]

# ------------------ MongoDB Utilities ------------------
def get_db():
    client = MongoClient(st.secrets["MONGO_URI"])
    db = client['finance_ai']
    return db, client

def add_transaction(transactions):
    client = MongoClient(st.secrets["MONGO_URI"])
    db = client['finance_ai']
    collection = db['transactions']
    collection.insert_one(transactions)
    client.close()

def get_transactions(user_id):
    client = MongoClient(st.secrets["MONGO_URI"])
    db = client['finance_ai']
    collection = db['transactions']
    transactions = list(collection.find({"user_id": user_id}))
    client.close()
    return transactions

def auto_add_subscriptions(user_id):
    client = MongoClient(st.secrets["MONGO_URI"])
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
    
# ------------------ Get Recommendations ------------------
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def fetch_recommendations(user_id):
    try:
        response = requests.post(
            url=f"{BACKEND_URL}/get-recommendations",
            json={"user_id": user_id},
            timeout=60
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.json().get("error", "Unknown error")}
    except Exception as e:
        return {"error": str(e)}
    
# Typing animation function
def typewriter_effect(text, delay=0.005, is_markdown=True):
    placeholder = st.empty()
    typed_text = ""
    for char in text:
        typed_text += char
        if is_markdown:
            placeholder.markdown(typed_text, unsafe_allow_html=True)
        else:
            placeholder.write(typed_text)
        time.sleep(delay)

def update_user_profile(user_id, amount, amount_type, transaction_mode, category=None):
    db, client = get_db()
    profile = db['user_profiles'].find_one({"user_id": user_id})
    if not profile:
        client.close()
        return

    cash = float(profile.get("cash_holdings", 0))
    online = float(profile.get("online_holdings", 0))
    stock = float(profile.get("stock_investments", 0))
    savings = float(profile.get("savings", 0))
    total_savings = float(profile.get("total_savings", 0))

    if transaction_mode == "cash" and category != "Savings":
        if amount_type == "credit":
            cash += amount
        else:
            cash = max(0, cash - amount)

    elif transaction_mode == "online":
        if amount_type == "credit":
            online += amount
        else:
            online = max(0, online - amount)

    elif transaction_mode == "stock":
        if amount_type == "debit":
            stock += amount
            online = max(0, online - amount)
        else:
            online += amount
            stock = max(0, stock - amount)

    elif category == "Savings" and transaction_mode == "cash":
        savings += amount
        
    total_savings = stock + savings

    db['user_profiles'].update_one(
        {"user_id": user_id},
        {"$set": {
            "cash_holdings": cash,
            "online_holdings": online,
            "stock_investments": stock,
            "savings": savings,
            "total_savings": total_savings
        }}
    )
    client.close()

# ------------------ Main Page ------------------
def home_page(user_id):
    st.title("💰 Personal Finance Tracker")

    with st.expander("➕ Add New Transaction", expanded=True):
        # Step 1: Fetch categories for current user
        all_categories = get_user_categories(user_id)
        if not all_categories:
            all_categories = [
                "Food", "Travel", "Rent", "Salary", "Shopping",
                "Healthcare", "Utilities", "Miscellaneous", "Savings"
            ]

        # Step 2: Show Add Custom Category Form
        with st.form("add_custom_category_form"):
            st.markdown("### ➕ Add a New Custom Category")
            new_category = st.text_input("Enter new category name")
            add_btn = st.form_submit_button("Add Category")

            if add_btn:
                new_category = new_category.strip()
                if new_category:
                    result = add_custom_category(user_id, new_category)
                    if result == "duplicate":
                        st.warning("⚠️ This category already exists.")
                    else:
                        st.success("✅ Category added successfully!")
                        st.rerun()
                else:
                    st.warning("⚠️ Category cannot be empty.")

        # Step 3: Transaction Form
        st.markdown("### 📥 Record a Transaction")
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("📅 Date", value=datetime.today())
            category = st.selectbox("📂 Category", all_categories)
        with col2:
            amount = st.number_input("💸 Amount", min_value=0.0, format="%.2f")
            amount_type = st.radio("📈 Type", ["Income", "Expense"], horizontal=True)

        transaction_mode = st.selectbox("💳 Transaction Mode", ["cash", "online", "stock"])
        description = st.text_input("📝 Description")

        if st.button("✅ Add Transaction"):
            trans_type = "credit" if amount_type == "Income" else "debit"
            transaction = {
                "user_id": user_id,
                "transaction_date": date.strftime("%Y-%m-%d"),
                "amount": amount,
                "amount_type": trans_type,
                "category": category,
                "transaction_mode": transaction_mode,
                "description": description,
                "type": "manual"
            }
            add_transaction(transaction)
            update_user_profile(user_id, amount, trans_type, transaction_mode, category=category)
            st.success("🎉 Transaction added successfully!")
            
    # ========== Section 2: Upload Receipt ==========
    with st.expander("📸 Upload and Parse Receipt"):
        uploaded_file = st.file_uploader("Upload receipt image", type=["png", "jpg", "jpeg"])
        category = st.selectbox("Select receipt category", ["Groceries", "Bills", "Utilities", "Shopping", "Others"])

        if st.button("📤 Parse Receipt"):
            if uploaded_file is not None:
                # Convert image to base64
                image_bytes = uploaded_file.read()
                base64_image = base64.b64encode(image_bytes).decode('utf-8')
                image_url = f"data:image/jpeg;base64,{base64_image}"

                payload = {
                    "image_url": image_url,
                    "user_id": user_id,
                    "category": category.lower()
                }

                try:
                    response = requests.post(f"{BACKEND_URL}/parse-receipt", json=payload)
                    if response.status_code == 200:
                        st.success("🧾 Receipt parsed and transaction added successfully!")
                    else:
                        st.error(f"❌ Error: {response.json().get('error')}")
                except Exception as e:
                    st.error(f"⚠️ API call failed: {str(e)}")
            else:
                st.warning("📎 Please upload a receipt image first.")

    # ------------------ Transaction History ------------------
    st.subheader("📊 Transaction History")

    transactions = get_transactions(user_id)
    
    auto_add_subscriptions(user_id)

    if transactions:
        # Convert to DataFrame for formatting
        df = pd.DataFrame(transactions)
        df = df.drop(columns=["_id", "user_id"])

        df["transaction_date"] = pd.to_datetime(df["transaction_date"])
        
        df.sort_values(by="transaction_date", ascending=False, inplace=True)
        
        # Format the date
        df["transaction_date"] = df["transaction_date"].dt.strftime("%b %d, %Y")

        # Color styling
        def highlight_type(val):
            color = "lightgreen" if val == "credit" else "salmon"
            return f"background-color: {color}"

        st.dataframe(
            df.style.applymap(highlight_type, subset=["amount_type"]),
            use_container_width=True,
            height=400
        )
        
    else:
        st.info("No transactions recorded yet. Add your first transaction above! 🚀")