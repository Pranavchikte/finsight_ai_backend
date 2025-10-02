from datetime import datetime

PREDEFINED_CATEGORIES = {
    "Food & Dining",
    "Transportation",
    "Utilities",
    "Housing",
    "Shopping",
    "Entertainment",
    "Health & Wellness",
    "Groceries",
    "Bills & Fees",
    "Travel",
    "Education",
    "Other"
}

class Transaction:
    @staticmethod
    def create_transaction(user_id, amount, category, description, date=None):
        if category not in PREDEFINED_CATEGORIES:
            return None
        
        if not isinstance(amount, (int, float)) or amount <= 0:
            return None
        
        return {
            "user_id": user_id,
            "amount": amount,
            "category": category,
            "description": description,
            "date": date or datetime.utcnow(),
            "status": "completed",
        }
        
    @staticmethod
    def create_ai_transaction(user_id, text):
        return {
            "user_id": user_id,
            "raw_text": text,
            "description": f"Processing: {text[:40]}...",
            "amount": 0, 
            "category": "Other", 
            "date": datetime.utcnow(),
            "status": "processing",
        }