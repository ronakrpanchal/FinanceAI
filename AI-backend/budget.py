from typing import List, Optional
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
from dotenv import load_dotenv
import os
from pymongo import MongoClient

load_dotenv()

API_KEY = os.environ.get("GROQ_API_KEY")
MODEL_NAME = os.environ.get('MODEL_NAME')
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')

class BudgetCategory(BaseModel):
    category: str
    allocated_amount: float
    # actual_spent: Optional[float] = 0.0

class Budget(BaseModel):
    income: float
    savings: float
    expenses: List[BudgetCategory]

def load_model():
    llm = ChatGroq(
        model_name=MODEL_NAME,
        temperature=0.7,
        api_key=API_KEY
    )

    parser = JsonOutputParser(pydantic_object=Budget)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Extract budget details into JSON with this structure:
            {{
                "income": income_value,
                "savings": savings_value,
                "expenses": [
                    {{"category": "category_name", "allocated_amount": amount}}
                ]
            }}"""),
        ("user", "{input}")
    ])

    chain = prompt | llm | parser
    
    return chain

def save_json_to_file(data, filename):
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=2)

def parse_budget(description: str) -> dict:
    chain_ = load_model()
    result = chain_.invoke({"input": description})
    save_json_to_file(result, 'budget_data.json')
    return result

def get_mongodb_connection():
    """Create and return a MongoDB client connection"""
    client = MongoClient(MONGO_URI)
    return client

def save_in_db(user_id, response):
    """Save budget data to MongoDB"""
    client = get_mongodb_connection()
    db = client['finance_ai']  # Database name
    budgets_collection = db['budgets']  # Collection name
    
    # Create document to insert
    budget_document = {
        'user_id': user_id,
    }
    new_budget = {
        '$set': {
            'budget_data': response
        }
    }
    # Insert document into collection
    budgets_collection.update_one(budget_document,update=new_budget, upsert=True)
    client.close()
    
    # return result.inserted_id

def get_user_budget(user_id):
    """Retrieve user budget from MongoDB"""
    client = get_mongodb_connection()
    db = client['finance_ai']
    budgets_collection = db['budgets']
    
    budget = budgets_collection.find_one({'user_id': user_id})
    client.close()
    
    return budget

if __name__ == "__main__":
    response = parse_budget("I earn 5000 per month. I allocate 2000 for rent, 500 for groceries, 300 for utilities, and 500 for entertainment. I save 1000 each month.")
    print(response)
    inserted_id = save_in_db('68245ee0af6dbf213330448c', response)
    print(f"Budget data saved successfully with ID: {inserted_id}")