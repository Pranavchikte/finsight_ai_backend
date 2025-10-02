from app import celery
from app import mongo
from bson import ObjectId
from app.services.gemini_service import parse_expense_test

@celery.task
def process_ai_transaction(transaction_id: str):
    
    try:
        transaction = mongo.db.transactions.find_one({"_id": ObjectId(transaction_id)})
        if not transaction:
            print(f"Transaction with ID {transaction_id} not found.")
            return

        raw_text = transaction.get("raw_text")
        if not raw_text:
            raise ValueError("Transaction is missing raw_text for AI processing.")

        parsed_data = parse_expense_test(raw_text)

        if not parsed_data:
            mongo.db.transactions.update_one(
                {"_id": ObjectId(transaction_id)},
                {"$set": {"status": "failed", "failure_reason": "AI could not parse the expense."}}
            )
            return

        update_fields = {
            "amount": parsed_data.get("amount"),
            "category": parsed_data.get("category"),
            "description": parsed_data.get("description"),
            "status": "completed"
        }
        mongo.db.transactions.update_one(
            {"_id": ObjectId(transaction_id)},
            {"$set": update_fields}
        )
        print(f"Successfully processed transaction {transaction_id}")

    except Exception as e:
        mongo.db.transactions.update_one(
            {"_id": ObjectId(transaction_id)},
            {"$set": {"status": "failed", "failure_reason": str(e)}}
        )
        print(f"Failed to process transaction {transaction_id}: {e}")