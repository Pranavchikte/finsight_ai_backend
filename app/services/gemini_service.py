import os 
import json
import google.generativeai as genai
from app.transactions.schemas import PREDEFINED_CATEGORIES

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
        cleaned_response = response.text.strip().lstrip('```json').rstrip('```').strip()
        parsed_json = json.loads(cleaned_response)
        
        amount = parsed_json.get('amount')
        if not amount or not isinstance(amount, (int, float)) or amount <= 0:
            return None
        
        if all(k in parsed_json for k in ['amount', 'category', 'description']):
            return parsed_json
        return None
    
    except (json.JSONDecodeError, Exception) as e:
        print(f"Gemini service error: {e}") # Added a print statement for better debugging
        return None

def generate_spending_summary(spending_data: list) -> str | None:
    """
    Generates a brief, insightful summary of spending habits using the Gemini API.

    Args:
        spending_data: A list of dictionaries, where each dict is 
                       {'category': 'Some Category', 'total': 123.45}.
    
    Returns:
        A string containing the AI-generated summary, or None on failure.
    """
    if not spending_data:
        return "No spending data available for this period."

    data_json = json.dumps(spending_data, indent=2)

    prompt = f"""
    You are a friendly and insightful financial assistant called FinSight AI.
    Your task is to analyze a user's spending data for the past month and provide a brief, helpful summary (around 3-4 sentences).

    Rules:
    1.  Your tone should be encouraging and helpful, not judgmental.
    2.  Start with a general observation about their spending.
    3.  Identify the top 1 or 2 spending categories.
    4.  Offer one simple, actionable tip for potential savings based on their data.
    5.  Do not include any introductory or concluding pleasantries like "Hello" or "Let me know...". Just provide the summary.

    Here is the user's spending data by category in JSON format:
    {data_json}

    Now, generate the summary.
    """
    
    try:
        response = model.generate_content(prompt)
        # Add some basic cleaning to the response text
        summary = response.text.strip().replace('**', '') # Remove markdown bolding
        return summary
    except Exception as e:
        print(f"Gemini summary generation error: {e}")
        return None