from datetime import datetime

class Transaction:
    @staticmethod
    def create_transaction(user_id, amount, category, description, date=None):
        
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