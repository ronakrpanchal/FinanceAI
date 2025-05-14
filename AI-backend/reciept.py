import cv2
import pytesseract
import json
from pydantic import BaseModel
from typing import List
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
import os
from datetime import datetime
from pymongo import MongoClient

# Load environment variables
load_dotenv()
API_KEY = os.environ.get("GROQ_API_KEY")
MODEL_NAME = os.environ.get("MODEL_NAME")
MONGODB_URI = os.environ.get("MONGODB_URI")  # Add this in your .env file

# 📦 Define Product & Receipt data structures
class Product(BaseModel):
    name: str
    price: float

class ParsedReceiptData(BaseModel):
    products: List[Product]

# 🔗 LangChain LLM pipeline
def load_model():
    llm = ChatGroq(
        model_name=MODEL_NAME,
        temperature=0,
        api_key=API_KEY
    )

    parser = JsonOutputParser(pydantic_object=ParsedReceiptData)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Extract all product names and prices from the receipt in the following JSON format:
        {{
            "products": [
                {{"name": "product1", "price": 10.99}},
                {{"name": "product2", "price": 5.49}}
            ]
        }}
        Only include actual items. Don't include totals or taxes.
        """),
        ("user", "{input}")
    ])

    return prompt | llm | parser

# 🖼️ Image preprocessing
def preprocess_receipt(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    processed = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY, 11, 2)
    return processed

# 🧾 OCR text extraction
def extract_text_from_receipt(image_path):
    processed_image = preprocess_receipt(image_path)
    extracted_text = pytesseract.image_to_string(processed_image)
    return extracted_text

# 🔍 Query LLM to get structured JSON
def query_llm(extracted_text):
    chain = load_model()
    result: ParsedReceiptData = chain.invoke({"input": extracted_text})
    return result

# 💾 Save JSON response to file
def save_json_to_file(data, filename):
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=2)

# 🧠 Main pipeline
def receipt_model(image_path):
    extracted_text = extract_text_from_receipt(image_path)
    llm_response = query_llm(extracted_text)
    save_json_to_file(llm_response, filename="llm_response.json")
    return llm_response

# 🗃️ Save to MongoDB
def save_receipt_in_mongodb(user_id, llm_response: ParsedReceiptData, date, category):
    client = MongoClient(MONGODB_URI)
    db = client["finance_ai"]
    collection = db["transactions"]
    
    print(llm_response)

    documents = []
    for item in llm_response['products']:
        doc = {
            "user_id": user_id,
            "transaction_date": date,
            "amount": float(item['price']),
            "amount_type": "debit",
            "category": category,
            "description": item['name']
        }
        documents.append(doc)

    collection.insert_many(documents)
    client.close()

# 🧪 Test runner
if __name__ == "__main__":
    result = receipt_model("/Applications/Projects/Financial Recommender/FinanceAI/receipt-ocr-original.jpg")
    save_receipt_in_mongodb('68245ee0af6dbf213330448c', result, datetime.now().strftime("%Y-%m-%d"), "groceries")
    print("✅ Saved to MongoDB and llm_response.json")