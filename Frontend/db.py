from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection string (replace with your own)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

def create_mongodb_structure():
    """Create MongoDB database and collections"""
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URI)
        
        # Create or access the database
        db = client["finance_ai"]
        
        # Create collections (equivalent to tables in SQL)
        users_collection = db["users"]
        transactions_collection = db["transactions"]
        subscriptions_collection = db["subscriptions"]
        debts_collection = db["debts"]
        budgets_collection = db["budgets"]
        
        # Create indexes for faster queries
        users_collection.create_index("username", unique=True)
        transactions_collection.create_index("user_id")
        subscriptions_collection.create_index("user_id")
        debts_collection.create_index("user_id")
        budgets_collection.create_index("user_id", unique=True)
        
        print("MongoDB database and collections created successfully")
        
        # # Example document structures (as a reference)
        # example_user = {
        #     "username": "example_user",
        #     "password": "hashed_password"  # In production, always store hashed passwords
        # }
        
        # example_transaction = {
        #     "user_id": "user_id_reference",
        #     "transaction_date": "2025-05-14",
        #     "amount": 150.00,
        #     "amount_type": "expense",  # or "income"
        #     "category": "Groceries",
        #     "description": "Weekly grocery shopping"
        # }
        
        # example_subscription = {
        #     "user_id": "user_id_reference",
        #     "name": "Netflix",
        #     "cost": 15.99,
        #     "usage": "Daily",  # One of: Daily, Weekly, Monthly, Rarely
        #     "priority": "Medium",  # One of: High, Medium, Low
        #     "created_at": "2025-05-14T12:00:00Z"
        # }
        
        # example_debt = {
        #     "user_id": "user_id_reference",
        #     "name": "Car Loan",
        #     "amount": 12000.00,
        #     "interest_rate": 4.5,
        #     "priority": "High",  # One of: High, Medium, Low
        #     "created_at": "2025-05-14T12:00:00Z"
        # }
        
        # example_budget = {
        #     "user_id": "user_id_reference",
        #     "budget_data": {
        #         "monthly_income": 5000.00,
        #         "savings_goal": 1000.00,
        #         "expense_categories": {
        #             "Housing": 1500.00,
        #             "Food": 600.00,
        #             "Transportation": 300.00,
        #             "Entertainment": 200.00,
        #             "Other": 400.00
        #         }
        #     }
        # }
        
        # # Print example documents for reference
        # print("\nExample document structures:")
        # print("\nUser document:")
        # print(example_user)
        # print("\nTransaction document:")
        # print(example_transaction)
        # print("\nSubscription document:")
        # print(example_subscription)
        # print("\nDebt document:")
        # print(example_debt)
        # print("\nBudget document:")
        # print(example_budget)
        
        return db
    
    except Exception as e:
        print(f"Error creating MongoDB database: {e}")
        return None

if __name__ == "__main__":
    create_mongodb_structure()