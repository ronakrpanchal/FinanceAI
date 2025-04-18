import pandas as pd
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
import os
import sqlite3
from datetime import datetime, timedelta

load_dotenv()

API_KEY = os.environ.get("GROQ_API_KEY")
MODEL_NAME = os.environ.get('MODEL_NAME')

def preprocess(user_id):
    """Preprocess user data from the database"""
    conn = sqlite3.connect('finance_ai.db')
    
    try:
        # Get current month's transactions
        current_month = datetime.now().strftime('%Y-%m')
        query = """
            SELECT transaction_date, amount, amount_type, category, description 
            FROM transactions 
            WHERE user_id = ? 
            AND strftime('%Y-%m', transaction_date) = ?
        """
        df = pd.read_sql_query(query, conn, params=(user_id, current_month))
        
        # Get subscriptions with their usage and priority
        subscriptions_query = """
            SELECT name, cost, usage, priority 
            FROM subscriptions 
            WHERE user_id = ?
        """
        subscriptions_df = pd.read_sql_query(subscriptions_query, conn, params=(user_id,))
        subscriptions = subscriptions_df.to_dict('records')
        
        # Get debts with interest rates
        debts_query = """
            SELECT name, amount, interest_rate, priority 
            FROM debts 
            WHERE user_id = ?
        """
        debts_df = pd.read_sql_query(debts_query, conn, params=(user_id,))
        debts = debts_df.to_dict('records')
        
        # Get budget data
        budget_query = """
            SELECT budget_data 
            FROM budgets 
            WHERE user_id = ? 
        """
        cursor = conn.cursor()
        cursor.execute(budget_query, (user_id,))
        result = cursor.fetchone()
        
        # Calculate financial metrics
        ESSENTIAL_CATEGORIES = ["Rent", "Utilities", "Healthcare"]
        VARIABLE_CATEGORIES = ["Dining", "Shopping", "Entertainment"]
        
        # Income and expenses
        total_income = df[df["amount_type"] == "credit"]["amount"].sum()
        fixed_expenses = df[df["category"].isin(ESSENTIAL_CATEGORIES)]["amount"].sum()
        
        # Variable expenses by category
        variable_expenses = df[df["category"].isin(VARIABLE_CATEGORIES)]
        variable_expenses_summary = variable_expenses.groupby("category")["amount"].sum().to_dict()
        
        # Subscription costs
        total_subscription_cost = sum(sub['cost'] for sub in subscriptions)
        
        # Debt calculations
        total_debt = sum(debt['amount'] for debt in debts)
        weighted_interest_rate = sum(
            debt['amount'] * debt['interest_rate'] for debt in debts
        ) / total_debt if total_debt > 0 else 0
        
        # Parse budget data
        budget_data = json.loads(result[0]) if result else {
            "income": 0,
            "savings": 0,
            "expenses": []
        }
        
        # Prepare comprehensive user data
        user_data_json = {
            "financial_summary": {
                "total_income": total_income,
                "fixed_expenses": fixed_expenses,
                "variable_expenses": variable_expenses_summary,
                "total_subscription_cost": total_subscription_cost,
                "total_debt": total_debt,
                "weighted_interest_rate": weighted_interest_rate,
                "budget": {
                    "income": budget_data.get("income", 0),
                    "savings": budget_data.get("savings", 0),
                    "expenses": budget_data.get("expenses", [])
                }
            },
            "subscriptions": subscriptions,
            "debts": debts,
            "monthly_trends": {
                "income_trend": calculate_trend(conn, user_id, "credit"),
                "expense_trend": calculate_trend(conn, user_id, "debit")
            }
        }
        
        return user_data_json
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def calculate_trend(conn, user_id, amount_type):
    """Calculate monthly trends for income or expenses"""
    query = """
        SELECT strftime('%Y-%m', transaction_date) as month,
               SUM(amount) as total
        FROM transactions
        WHERE user_id = ? AND amount_type = ?
        GROUP BY month
        ORDER BY month DESC
        LIMIT 3
    """
    df = pd.read_sql_query(query, conn, params=(user_id, amount_type))
    return df.to_dict('records')

def load_model():
    llm = ChatGroq(
        model_name=MODEL_NAME,
        temperature=0.7,
        api_key=API_KEY
    )

    parser = JsonOutputParser(pydantic_object={
        "type": "object",
        "properties": {
            "recommendations": {
                "type": "array",
                "items": {"type": "string"}
            },
            "action_items": {
                "type": "array",
                "items": {"type": "string"}
            },
            "risk_assessment": {
                "type": "object",
                "properties": {
                    "debt_risk": {"type": "string"},
                    "savings_risk": {"type": "string"},
                    "subscription_risk": {"type": "string"}
                }
            }
        }
    })

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Analyze the user's financial data and provide comprehensive recommendations.
            Consider their income, expenses, subscriptions, debts, and savings goals.
            Focus on actionable insights and risk assessment.
            
            Data Structure:
            {user_data_json}
            
            Provide recommendations in this format:
            {{
                "recommendations": ["specific recommendation 1", "recommendation 2"],
                "action_items": ["immediate action 1", "action 2"],
                "risk_assessment": {{
                    "debt_risk": "assessment of debt situation",
                    "savings_risk": "assessment of savings progress",
                    "subscription_risk": "assessment of subscription costs"
                }}
            }}"""),
        ("user", "{user_data_json}")
    ])

    chain = prompt | llm | parser
    return chain

def get_recommendations(user_data_json: dict) -> dict:
    chain_ = load_model()
    result = chain_.invoke({"user_data_json": json.dumps(user_data_json, indent=2)})
    return result

# def save_recommendations(user_id: int, recommendations: dict):
#     """Save recommendations to the database"""
#     conn = sqlite3.connect('finance_ai.db')
#     cursor = conn.cursor()
    
#     try:
#         # Add timestamp to recommendations
#         recommendations['generated_at'] = datetime.now().isoformat()
        
#         cursor.execute("""
#             INSERT INTO budgets (user_id, budget_data)
#             VALUES (?, ?)
#         """, (user_id, json.dumps(recommendations)))
        
#         conn.commit()
#         print("Successfully saved recommendations")
        
#     except sqlite3.Error as e:
#         print(f"An error occurred: {e}")
#         conn.rollback()
#     finally:
#         conn.close()

def financial_recommender(user_id: int):
    """Main function to generate and save financial recommendations"""
    # Get user data
    user_data_json = preprocess(user_id)
    if not user_data_json:
        return {"error": "Failed to process user data"}
    
    # Get recommendations
    recommendations = get_recommendations(user_data_json)
    
    # Save recommendations
    
    return recommendations

if __name__ == "__main__":
    user_id = 1  # Replace with actual user ID
    recommendations = financial_recommender(user_id)
    print("Financial Recommendations:")
    print(json.dumps(recommendations, indent=2))