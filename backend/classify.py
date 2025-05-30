# backend/classify.py

import pandas as pd
import requests
import json
import re
import os
from dotenv import load_dotenv

load_dotenv()

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct"

# Define your categories globally
CATEGORIES = [
    'Groceries', 'Dining', 'Transport', 'Reimbursement',
    'Salary', 'Entertainment', 'Shopping', 'Bills', 'Other'
]

def hf_llama_classify(description: str, amount: float) -> tuple[str, float]:
    prompt = (
        "Classify the following bank transaction into one of the categories below. "
        "Use both the description and amount to make your decision. "
        "Note: Positive amounts are credits (e.g. income, reimbursements), negative amounts are debits (e.g. purchases, bills).\n\n"
        f"Categories: {', '.join(CATEGORIES)}\n\n"
        "Respond ONLY in this format:\n"
        "Category: <category>, Confidence: <0-1>\n\n"
        "Examples:\n"
        "STOP & SHOP 06, Amount: -35.23 → Category: Groceries, Confidence: 0.95\n"
        "WALMART SUPERCENTER, Amount: -52.87 → Category: Groceries, Confidence: 0.95\n"
        "PAYPAL *LYFT TEMP AUTH, Amount: -12.84 → Category: Transport, Confidence: 0.90\n"
        "VENMO FROM JOHN, Amount: +18.00 → Category: Reimbursement, Confidence: 0.90\n"
        "PAYCHECK ACME CORP, Amount: +2000.00 → Category: Salary, Confidence: 0.98\n"
        "NETFLIX.COM BILLING, Amount: -15.99 → Category: Entertainment, Confidence: 0.95\n"
        "E-ZPASS REPLENISHMENT, Amount: -50.00 → Category: Bills, Confidence: 0.88\n\n"
        f"Transaction: \"{description}\", Amount: {amount:.2f}\n"
        "Response:"
    )

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 32,
            "temperature": 0.2
        }
    }

    response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
    try:
        response.raise_for_status()
        result = response.json()
        if isinstance(result, list) and 'generated_text' in result[0]:
            full_response = result[0]['generated_text']
        else:
            full_response = str(result)
        matches = re.findall(r'Category:\s*([A-Za-z]+),\s*Confidence:\s*([0-9.]+)', full_response)
        if matches:
            category, confidence = matches[-1]
            return category.strip(), float(confidence)
        else:
            return "Other", 0.5
    except Exception as e:
        print(f"❌ API Error: {e}\nRaw response: {response.text}")
        return "Other", 0.5

def classify_transactions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    categories = []
    confidences = []

    for _, row in df.head(3).iterrows():
        cat, conf = hf_llama_classify(row['description'], row['amount'])
        categories.append(cat)
        confidences.append(conf)

    df['category'] = categories
    df['confidence'] = confidences
    df['is_reimbursement'] = df['category'].str.lower() == 'reimbursement'

    return df
