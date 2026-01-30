from datetime import datetime, timezone

class Transaction:
    @staticmethod
    def create_transaction(user_id, amount, category, description, date=None):
        return {
            "user_id": user_id,
            "amount": amount,
            "category": category,
            "description": description,
            "date": date if date else datetime.now(timezone.utc),
            "status": "completed",
        }
        
    @staticmethod
    def create_ai_transaction(user_id, text, date=None):
        return {
            "user_id": user_id,
            "raw_text": text,
            "description": f"Processing: {text[:40]}...",
            "amount": 0, 
            "category": "Other", 
            "date": date if date else datetime.now(timezone.utc),
            "status": "processing",
        }