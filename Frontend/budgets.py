import streamlit as st
from pymongo import MongoClient
import pandas as pd

def budget_planning_page(user_id):
    st.title("Budget Planning")

    # MongoDB connection
    client = MongoClient('mongodb://localhost:27017/')
    db = client['finance_ai']
    budgets_collection = db['budgets']
    transactions_collection = db['transactions']

    # Define categories
    categories = ['Housing', 'Food', 'Transportation', 'Entertainment', 'Other']

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

        amount = st.number_input(f"Budget for {category}", min_value=0.0, step=100.0, format="%.2f", value=default_val, key=category)

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
    
    # Budget vs Expenses
    st.subheader("Budget vs. Expenses")
    expenses_df = pd.DataFrame(list(transactions_collection.find({'user_id': user_id, 'amount_type': 'expense'})))

    if not expenses_df.empty:
        # Step 1: Normalize and map subcategories
        expenses_df['category'] = expenses_df['category'].str.strip().str.capitalize()

        # Mapping subcategories (you can expand this as needed)
        category_mapping = {
            "Groceries": "Food",
            "Dining": "Food",
            "Rent": "Housing",
            "Utilities": "Housing",
            "Fuel": "Transportation",
            "Bus": "Transportation",
            "Movie": "Entertainment",
            "Concert": "Entertainment",
            # Add more mappings if needed
        }
        expenses_df['Mapped Category'] = expenses_df['category'].map(category_mapping).fillna('Others')

        # Step 2: Aggregate expenses
        total_exp = expenses_df.groupby('Mapped Category')['amount'].sum().abs().reset_index(name='Actual Expense (₹)')

        # Step 3: Load budget data
        budget_df = pd.DataFrame(user_budget['budget_data']['expenses'])
        budget_df.rename(columns={"category": "Mapped Category", "allocated_amount": "Budget (₹)"}, inplace=True)

        # Step 4: Merge and compute remaining & status
        comparison = pd.merge(budget_df, total_exp, on='Mapped Category', how='left').fillna(0)
        comparison['Remaining (₹)'] = comparison['Budget (₹)'] - comparison['Actual Expense (₹)']
        comparison['Status'] = comparison['Remaining (₹)'].apply(lambda x: "Over Budget" if x < 0 else "Within Budget")

        # Display result
        st.dataframe(comparison)

    else:
        st.info("No expenses recorded yet.")

    client.close()