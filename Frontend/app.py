import streamlit as st
from pymongo import MongoClient
import re
# import os
# from dotenv import load_dotenv
import bcrypt
from datetime import datetime
from db import create_mongodb_structure
from home import home_page
from budgets import budget_planning_page
from debts import debts_page
from subscriptions import subscription_page
from dashboard import render_dashboard
from bson import ObjectId

# Load environment variables
# load_dotenv()

# MongoDB connection string
# MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

MONGO_URI = st.secrets["MONGO_URI"]

# Initialize MongoDB client
try:
    client = MongoClient(MONGO_URI)
    db = client["finance_ai"]
    
    # Get collections
    users_collection = db["users"]
    transactions_collection = db["transactions"]
    subscriptions_collection = db["subscriptions"]
    debts_collection = db["debts"]
    budgets_collection = db["budgets"]
    user_profiles_collection = db["user_profiles"]
except Exception as e:
    st.error(f"Failed to connect to MongoDB: {e}")
    st.stop()

# Utility functions
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def is_strong_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    return True, "Password is strong"

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(provided_password, stored_password_hash):
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password_hash.encode('utf-8'))

# Authentication functions
def register_user(username, password, confirm_password):
    if not username or not password or not confirm_password:
        return False, "All fields are required"
    
    if not is_valid_email(username):
        return False, "Invalid email format"
    
    if password != confirm_password:
        return False, "Passwords do not match"
    
    password_strong, msg = is_strong_password(password)
    if not password_strong:
        return False, msg
    
    if users_collection.find_one({"username": username}):
        return False, "User already exists"
    
    try:
        hashed_password = hash_password(password)
        new_user = {
            "username": username,
            "password": hashed_password,
            "created_at": datetime.now()
        }
        result = users_collection.insert_one(new_user)
        if result.inserted_id:
            return True, "Registration successful!"
        else:
            return False, "Failed to register user"
    except Exception as e:
        return False, f"Registration error: {str(e)}"

def login_user(username, password):
    if not username or not password:
        return False, "Email and password are required"
    
    try:
        user = users_collection.find_one({"username": username})
        if not user:
            return False, "Invalid email or password"
        
        if check_password(password, user["password"]):
            st.session_state.authenticated = True
            st.session_state.user = {
                "id": str(user["_id"]),
                "email": user["username"]
            }
            return True, "Login successful"
        else:
            return False, "Invalid email or password"
    except Exception as e:
        return False, f"Login error: {str(e)}"

def logout_user():
    try:
        st.session_state.authenticated = False
        st.session_state.user = None
        return True, "Logged out successfully"
    except Exception as e:
        return False, f"Logout error: {str(e)}"
    
# Onboarding form after registration
def collect_initial_financial_info(user_id):
    st.title("Initial Financial Setup")

    with st.form("initial_financial_form"):
        cash = st.number_input("💵 Current Cash Holdings", min_value=0.0)
        online = st.number_input("🏦 Online Holdings (Bank, UPI, etc.)", min_value=0.0)
        stocks = st.number_input("📈 Investments in Stocks", min_value=0.0)
        savings = st.number_input("💰 Total Savings till now", min_value=0.0)
        submit = st.form_submit_button("Save and Continue")

        if submit:
            try:
                data = {
                    "user_id": user_id,
                    "cash_holdings": cash,
                    "online_holdings": online,
                    "stock_investments": stocks,
                    "total_savings": savings,
                    "created_at": datetime.now()
                }
                user_profiles_collection.insert_one(data)
                st.success("Information saved successfully!")
                st.session_state.authenticated = True
                st.session_state.user = {
                    "id": user_id,
                    "email": users_collection.find_one({"_id": ObjectId(user_id)})["username"]
                }
                st.session_state.current_page = "Home"
                del st.session_state.user_id_pending_info
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save data: {str(e)}")

# Streamlit app
def main():
    create_mongodb_structure()
    # st.set_page_config(
    #     page_title="Finance AI",
    #     page_icon="💰",
    #     layout="wide"
    # )
    
    # Session state init
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Home"
    if "auth_tab" not in st.session_state:
        st.session_state.auth_tab = "Sign In"
        
    if "user_id_pending_info" in st.session_state:
        collect_initial_financial_info(st.session_state.user_id_pending_info)
        return
    
    # Sidebar
    with st.sidebar:
        st.title("Finance AI")
        st.markdown("---")
        
        if st.session_state.authenticated:
            st.write(f"👤 {st.session_state.user['email']}")
            st.markdown("---")
            
            if st.button("🏠 Home", use_container_width=True):
                st.session_state.current_page = "Home"
                st.rerun()
                
            if st.button("💰 Budget Planning", use_container_width=True):
                st.session_state.current_page = "Budget Planning"
                st.rerun()
                
            if st.button("Debt Management", use_container_width=True):
                st.session_state.current_page = "Debt Management"
                st.rerun()
            
            if st.button("📅 Subscription Manager", use_container_width=True):
                st.session_state.current_page = "Subscription Manager"
                st.rerun()
                
            if st.button("📊 Dashboard", use_container_width=True):
                st.session_state.current_page = "Dashboard"
                st.rerun()
            
            st.markdown("---")
            if st.button("Sign Out", use_container_width=True):
                success, msg = logout_user()
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        else:
            st.info("Please sign in to access all features")
    
    # Main content
    if st.session_state.authenticated:
        if st.session_state.current_page == "Home":
            home_page(st.session_state.user["id"])
        elif st.session_state.current_page == "Budget Planning":
            budget_planning_page(st.session_state.user["id"])
        elif st.session_state.current_page == "Debt Management":
            debts_page(st.session_state.user["id"])
        elif st.session_state.current_page == "Subscription Manager":
            subscription_page(st.session_state.user["id"])
        elif st.session_state.current_page == "Dashboard":
            render_dashboard(st.session_state.user["id"])
    else:
        st.title("Welcome to Finance AI")
        
        tab1, tab2 = st.tabs(["Sign In", "Create Account"])
        
        if st.session_state.auth_tab == "Sign In":
            st.query_params['tab'] = "sign-in"
            tab = tab1
        else:
            st.query_params['tab'] = "create-account"
            tab = tab2
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                submit = st.form_submit_button("Sign In")
                if submit:
                    success, response = login_user(email, password)
                    if success:
                        st.success("Login successful!")
                        st.session_state.current_page = "Home"
                        st.rerun()
                    else:
                        st.error(response)
            if st.button("Forgot Password?"):
                st.session_state.show_reset = True
                st.rerun()
        
        with tab2:
            with st.form("register_form"):
                email = st.text_input("Email", key="register_email")
                password = st.text_input("Password", type="password", key="register_password")
                st.caption("Password must be at least 8 characters with uppercase, lowercase, and numbers")
                confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
                submit = st.form_submit_button("Create Account")
                if submit:
                    success, msg = register_user(email, password, confirm_password)
                    if success:
                        st.success(msg)
                        st.session_state.auth_tab = "Sign In"
                        st.rerun()
                    else:
                        st.error(msg)

if __name__ == "__main__":
    main()