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
        
        if not isinstance(amount, (int, float)):
            return None
        
        transaction_doc = {
            "user_id": user_id,
            "amount": amount,
            "category": category,
            "description": description,
            "date": date or datetime.utcnow()
        }
        return transaction_doc