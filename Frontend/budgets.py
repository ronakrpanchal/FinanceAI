import streamlit as st
from pymongo import MongoClient
import pandas as pd
import requests

def budget_planning_page(user_id):
    
    BACKEND_URL = st.secrets["BACKEND_URL"]
    
    st.title("Budget Planning")

    # MongoDB connection
    client = MongoClient(st.secrets["MONGO_URI"])
    db = client['finance_ai']
    budgets_collection = db['budgets']
    transactions_collection = db['transactions']

    # Define categories
    categories = ['Housing', 'Food', 'Transportation', 'Entertainment', 'Other']
    
    with st.expander("🧠 Generate Budget from Prompt"):
        prompt = st.text_area("Describe your budgeting needs", placeholder="e.g. I earn ₹50000 per month and want to save ₹10000. Allocate the rest across housing, food, travel, and fun.")
        if st.button("🪄 Generate Budget from AI"):
            if prompt.strip() != "":
                payload = {
                    "user_id": user_id,
                    "description": prompt
                }
                try:
                    response = requests.post(f"{BACKEND_URL}/generate-budget", json=payload)
                    if response.status_code == 200:
                        st.success("🎯 Budget generated successfully using AI!")
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {response.json().get('error')}")
                except Exception as e:
                    st.error(f"⚠️ Request failed: {str(e)}")
            else:
                st.warning("✍️ Please enter a description prompt.")

    # Set Budget Section
    st.subheader("Set Your Budgets")

    user_budget = budgets_collection.find_one({"user_id": user_id})

    # Initialize budget data if not present
    if not user_budget:
        budgets_collection.insert_one({
            "user_id": user_id,
            "budget_data": {
                "income": 0,
                "savings": 0,
                "expenses": []
            }
        })
        user_budget = budgets_collection.find_one({"user_id": user_id})

    # Set income and savings
    income = st.number_input(
        "Monthly Income",
        min_value=float(0),
        step=float(500),
        format="%.2f",
        value=float(user_budget['budget_data'].get('income', 0.0))
    )

    savings = st.number_input(
        "Planned Savings",
        min_value=float(0),
        step=float(100),
        format="%.2f",
        value=float(user_budget['budget_data'].get('savings', 0.0))
    )

    if st.button("Save Income & Savings"):
        budgets_collection.update_one(
            {"user_id": user_id},
            {"$set": {
                "budget_data.income": income,
                "budget_data.savings": savings
            }}
        )
        st.success("Income and savings updated successfully.")

    # Set budget for each category
    for category in categories:
        existing_alloc = next((item for item in user_budget['budget_data']['expenses'] if item['category'] == category), None)
        default_val = existing_alloc['allocated_amount'] if existing_alloc else 0.0

        amount = st.number_input(f"Budget for {category}", min_value=float(0), step=float(100), format="%.2f", value=float(default_val), key=category)

        if st.button(f"Save Budget for {category}", key=f"save_{category}"):
            budgets_collection.update_one(
                {"user_id": user_id, "budget_data.expenses.category": category},
                {"$set": {"budget_data.expenses.$.allocated_amount": amount}}
            )
            # If not found (new category), add it
            budgets_collection.update_one(
                {"user_id": user_id, "budget_data.expenses.category": {"$ne": category}},
                {"$push": {"budget_data.expenses": {"category": category, "allocated_amount": amount}}}
            )
            st.success(f"Budget for {category} set to ₹{amount:.2f}")

    # View Current Budget
    st.subheader("View Your Budget Plan")

    user_budget = budgets_collection.find_one({"user_id": user_id})  # Re-fetch after updates
    budget_df = pd.DataFrame(user_budget['budget_data']['expenses'])
    if not budget_df.empty:
        budget_df.rename(columns={"category": "Category", "allocated_amount": "Budget (₹)"}, inplace=True)
        st.write(f"**Income:** ₹{user_budget['budget_data']['income']:.2f}")
        st.write(f"**Savings Goal:** ₹{user_budget['budget_data']['savings']:.2f}")
        st.dataframe(budget_df)
    else:
        st.info("No budget allocations yet.")
    
    # Budget vs Expenses - simplified version without Mapped Category
    st.subheader("Budget vs. Expenses")
    expenses_df = pd.DataFrame(list(transactions_collection.find({'user_id': user_id, 'amount_type': 'debit'})))

    if not expenses_df.empty:
        # Normalize categories
        expenses_df['category'] = expenses_df['category'].str.strip().str.capitalize()
        
        # Aggregate expenses by category
        total_exp = expenses_df.groupby('category')['amount'].sum().abs().reset_index(name='Actual Expense (₹)')
        
        # Load budget data
        budget_df = pd.DataFrame(user_budget['budget_data']['expenses'])
        
        if not budget_df.empty:
            # Rename columns for clarity
            budget_df.rename(columns={"category": "category", "allocated_amount": "Budget (₹)"}, inplace=True)
            
            # Merge budget and expenses on category
            comparison = pd.merge(budget_df, total_exp, on='category', how='outer').fillna(0)
            
            # Calculate remaining budget and status
            comparison['Remaining (₹)'] = comparison['Budget (₹)'] - comparison['Actual Expense (₹)']
            comparison['Status'] = comparison['Remaining (₹)'].apply(lambda x: "Over Budget" if x < 0 else "Within Budget")
            
            # Clean up column name
            comparison.rename(columns={"category": "Category"}, inplace=True)
            
            # Display result
            st.dataframe(comparison)
        else:
            st.info("No budget allocations yet.")
    else:
        st.info("No expenses recorded yet.")

    client.close()