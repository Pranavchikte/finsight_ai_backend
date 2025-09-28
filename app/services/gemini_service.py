import os 
import json
import google.generativeai as genai
from app.models.transaction import PREDEFINED_CATEGORIES

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

def parse_expense_test(text: str) -> dict | None:
    allowed_categories_str = ", ".join(f'"{cat}"' for cat in PREDEFINED_CATEGORIES)
    
    prompt = f"""
    You are an expert expense parsing assistant. Your task is to analyze the user's text and extract the expense details.
    
    Rules:
    1. You must extract three pieces of information: amount (as a float), category (as a string), and description (as a string).
    2. The category MUST be one of the following predefined values: [{allowed_categories_str}]. Do not create new categories. If the expense doesn't fit, choose 'Other'.
    3. The description should be a concise summary of the expense.
    4. Your final output MUST be a single, valid JSON object and nothing else. Do not wrap it in markdown or any other text.
    
    Example:
    User text: "lunch with the team yesterday for 1500.50 rupees at the cafe"
    Your output: {{"amount": 1500.50, "category": "Food & Dining", "description": "Lunch with team at the cafe"}}
    
    User text: "uber ride to the airport for 750rs"
    Your output: {{"amount": 750.00, "category": "Transportation", "description": "Uber ride to the airport"}}

    Now, parse the following text:
    "{text}"
    """
    
    try:
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        parsed_json = json.loads(cleaned_response)
        
        amount = parsed_json.get('amount')
        if not amount or not isinstance(amount, (int, float)) or amount <= 0:
            return None
        
        if all(k in parsed_json for k in ['amount', 'category', 'description']):
            return parsed_json
        return None
    
    except (json.JSONDecodeError, Exception):
        return None