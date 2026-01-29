from datetime import datetime, timedelta, timezone

# IST timezone helper
IST = timezone(timedelta(hours=5, minutes=30))

class Transaction:
    @staticmethod
    def create_transaction(user_id, amount, category, description, date=None):
        return {
            "user_id": user_id,
            "amount": amount,
            "category": category,
            "description": description,
            "date": date if date else datetime.now(IST),  # Store in IST
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
            "date": date if date else datetime.now(IST),  # Store in IST
            "status": "processing",
        }