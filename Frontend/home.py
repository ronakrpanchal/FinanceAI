import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import pandas as pd
import requests
import base64
import json
from bson import ObjectId
import time

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
            url="http://127.0.0.1:5000/get-recommendations",
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
                    response = requests.post("http://127.0.0.1:5000/parse-receipt", json=payload)
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
        # ------------------ Recommendation Section ------------------
    with st.expander("🤖 Want Some Recommendation?"):
        if st.button("💡 Get Recommendation"):
            with st.spinner("Analyzing your financial data..."):
                result = fetch_recommendations(user_id)

            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                res = result["response"]

                # Show Recommendations
                st.markdown("### 🧠 Smart Financial Recommendations")
                for idx, rec in enumerate(res["recommendations"], 1):
                    content = f"**{idx}.** {rec}"
                    typewriter_effect(content)

                # Show Action Items
                st.markdown("### 📌 Actionable Items")
                for idx, action in enumerate(res["action_items"], 1):
                    content = f"- {action}"
                    typewriter_effect(content)

                # Show Risk Assessment with formatting and typing effect
                # Risk Assessment section (plain formatting with typing effect)
                st.markdown("### 🚨 Risk Assessment")

                # Optional mapping for better readability
                risk_titles = {
                    "debt_risk": "Debt Risk",
                    "savings_risk": "Savings Risk",
                    "subscription_risk": "Subscription Risk"
                }

                for key, value in res["risk_assessment"].items():
                    title = risk_titles.get(key, key.replace("_", " ").title())
                    content = f"**{title}**: {value}"
                    typewriter_effect(content)