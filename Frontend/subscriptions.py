import streamlit as st
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

def subscription_page(user_id):
    st.title("📅 Subscription Manager")

    # MongoDB connection
    client = MongoClient("mongodb://localhost:27017/")
    db = client['finance_ai']
    subscriptions_collection = db['subscriptions']

    # Add Subscription
    st.subheader("➕ Add New Subscription")
    name = st.text_input("Subscription Name")
    cost = st.number_input("Monthly Cost (₹)", min_value=0.0, step=1.0, format="%.2f", key="new_cost")
    usage = st.selectbox("Usage Frequency", ["Daily", "Weekly", "Monthly", "Occasionally"], key="new_usage")
    priority = st.selectbox("Priority Level", ["High", "Medium", "Low"], key="new_priority")

    if st.button("Add Subscription"):
        new_sub = {
            "user_id": user_id,
            "name": name,
            "cost": cost,
            "usage": usage,
            "priority": priority,
            "created_at": datetime.now()
        }
        subscriptions_collection.insert_one(new_sub)
        st.success(f"Subscription to {name} added!")
        st.experimental_rerun()

    # View Subscriptions
    st.subheader("📋 Your Subscriptions")
    subs = list(subscriptions_collection.find({"user_id": user_id}))

    if 'edit_id' not in st.session_state:
        st.session_state.edit_id = None

    if subs:
        for sub in subs:
            sub_id = str(sub['_id'])
            st.markdown("---")
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.session_state.edit_id == sub_id:
                    # Render edit inputs
                    updated_cost = st.number_input("Cost", value=float(sub['cost']), step=1.0, key=f"cost_{sub_id}")
                    updated_priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=["High", "Medium", "Low"].index(sub['priority']), key=f"priority_{sub_id}")
                    updated_usage = st.selectbox("Usage", ["Daily", "Weekly", "Monthly", "Occasionally"], index=["Daily", "Weekly", "Monthly", "Occasionally"].index(sub['usage']), key=f"usage_{sub_id}")

                    if st.button("Save", key=f"save_{sub_id}"):
                        subscriptions_collection.update_one(
                            {"_id": ObjectId(sub_id)},
                            {"$set": {
                                "cost": updated_cost,
                                "priority": updated_priority,
                                "usage": updated_usage
                            }}
                        )
                        st.success(f"{sub['name']} updated.")
                        st.session_state.edit_id = None
                        st.experimental_rerun()

                    if st.button("Cancel", key=f"cancel_{sub_id}"):
                        st.session_state.edit_id = None
                        st.experimental_rerun()
                else:
                    # Normal view
                    st.markdown(f"**Name:** {sub['name']}")
                    st.markdown(f"**Cost:** ₹{sub['cost']}")
                    st.markdown(f"**Usage:** {sub['usage']}")
                    st.markdown(f"**Priority:** {sub['priority']}")
                    st.markdown(f"**Created At:** {sub['created_at']}")

            with col2:
                if st.session_state.edit_id != sub_id and st.button("Edit", key=f"edit_{sub_id}"):
                    st.session_state.edit_id = sub_id

                if st.button("Cancel Subscription", key=f"delete_{sub_id}"):
                    subscriptions_collection.delete_one({"_id": ObjectId(sub_id)})
                    st.warning(f"{sub['name']} subscription cancelled.")
                    if st.session_state.edit_id == sub_id:
                        st.session_state.edit_id = None
                    st.experimental_rerun()
    else:
        st.info("No subscriptions found.")

    client.close()