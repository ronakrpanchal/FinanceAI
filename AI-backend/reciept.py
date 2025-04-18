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
import sqlite3
from datetime import datetime
load_dotenv()

API_KEY = os.environ.get("GROQ_API_KEY")
MODEL_NAME = os.environ.get('MODEL_NAME')

def load_model():
    llm = ChatGroq(
        model_name=MODEL_NAME,
        temperature=0.7,
        api_key=API_KEY
    )

    parser = JsonOutputParser(pydantic_object={
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "price": {"type": "number"}
        }
    })

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Extract product details into JSON with this structure:
            {{
                "name": "product name here",
                "price": number_here_without_currency_symbol
            }}"""),
        ("user", "{input}")
    ])

    chain = prompt | llm | parser
    
    return chain 

class Product(BaseModel):
    name: str
    price: str

class ParsedReceiptData(BaseModel):
    products: List[Product]

def preprocess_receipt(image_path):

    image = cv2.imread(image_path)
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    processed = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY, 11, 2)
    return processed

def extract_text_from_receipt(image_path):
    processed_image = preprocess_receipt(image_path)
    
    extracted_text = pytesseract.image_to_string(processed_image)
    return extracted_text

def query_llm(extracted_text):
    chain_ = load_model()
    result = chain_.invoke({"input": extracted_text})
    return result

def save_json_to_file(data, filename):
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=2)

def reciept_model(image_path):
    extracted_text = extract_text_from_receipt(image_path)
    llm_response = query_llm(extracted_text)
    save_json_to_file(llm_response,filename="llm_response.json")
    return llm_response

def save_reciept_in_db(user_id,llm_response,date,type):
    conn = sqlite3.connect('finance_ai.db')
    cursor = conn.cursor()
    transactions = []
    for item in llm_response:
        transactions.append((user_id,date,float(item['price']),'debit',type,item['name']))
    cursor.executemany("INSERT INTO transactions (user_id,transaction_date,amount,amount_type,category,description) VALUES (?,?,?,?,?,?)", transactions)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    data=reciept_model("receipt-ocr-original.jpg")
    save_reciept_in_db(3,data,datetime.now().strftime("%Y-%m-%d"),"groceries")
    print("Saved to llm_response.json")