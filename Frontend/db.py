from pymongo import MongoClient
import streamlit as st

@st.cache_resource
def create_mongodb_structure():
    """Create MongoDB database and collections"""
    try:
        # Connect to MongoDB
        MONGO_URI = st.secrets['MONGO_URI'] 
        client = MongoClient(MONGO_URI)
        
        # Create or access the database
        db = client["finance_ai"]
        
        # Create collections (equivalent to tables in SQL)
        users_collection = db["users"]
        transactions_collection = db["transactions"]
        subscriptions_collection = db["subscriptions"]
        debts_collection = db["debts"]
        budgets_collection = db["budgets"]
        user_profiles_collection = db["user_profiles"]
        monthly_budgets_collection = db["monthly_budgets"]
        
        # Create indexes for faster queries
        users_collection.create_index("username", unique=True)
        transactions_collection.create_index("user_id")
        subscriptions_collection.create_index("user_id")
        debts_collection.create_index("user_id")
        budgets_collection.create_index("user_id", unique=True)
        user_profiles_collection.create_index("user_id", unique=True)
        monthly_budgets_collection.create_index("user_id", unique=True)
        
        print("MongoDB database and collections created successfully")
        return db
    
    except Exception as e:
        print(f"Error creating MongoDB database: {e}")
        return None