# utils/categories.py
from pymongo import MongoClient
import streamlit as st

MONGO_URI = st.secrets["MONGO_URI"]

client = MongoClient(MONGO_URI)  # or your connection
db = client["finance_ai"]
user_profiles_collection = db["user_profiles"]

PREDEFINED_CATEGORIES = [
    "Food", "Travel", "Rent", "Salary", "Shopping",
    "Healthcare", "Utilities", "Miscellaneous", "Savings"
]

def get_user_categories(user_id):
    profile = user_profiles_collection.find_one({"user_id": user_id})
    return profile.get("custom_categories", []) if profile else []

def add_custom_category(user_id, category):
    if not category:
        return "empty"
    profile = user_profiles_collection.find_one({"user_id": user_id})
    existing = profile.get("custom_categories", []) if profile else []
    if category in existing:
        return "duplicate"
    user_profiles_collection.update_one(
        {"user_id": user_id},
        {"$addToSet": {"custom_categories": category}},
        upsert=True
    )
    return "success"