from flask import current_app
from app import celery
from app import mongo
from bson import ObjectId
from app.services.gemini_service import parse_expense_test

@celery.task
def process_ai_transaction(transaction_id: str):
    """
    Celery task to process a transaction using the Gemini AI service.
    Logs the outcome of the operation.
    """
    logger = current_app.logger  # Get the configured Flask logger

    try:
        transaction = mongo.db.transactions.find_one({"_id": ObjectId(transaction_id)})
        if not transaction:
            logger.error(f"AI_TASK_FAIL: Transaction with ID {transaction_id} not found.")
            return

        raw_text = transaction.get("raw_text")
        if not raw_text:
            # This is a critical error, so we log it as such
            logger.error(f"AI_TASK_FAIL: Transaction {transaction_id} is missing raw_text for AI processing.")
            raise ValueError("Transaction is missing raw_text for AI processing.")

        # Log that we are starting the API call
        logger.info(f"AI_TASK_START: Calling Gemini API for transaction {transaction_id}.")
        parsed_data = parse_expense_test(raw_text)

        if not parsed_data:
            mongo.db.transactions.update_one(
                {"_id": ObjectId(transaction_id)},
                {"$set": {"status": "failed", "failure_reason": "AI could not parse the expense."}}
            )
            logger.warning(f"AI_TASK_FAIL: Gemini could not parse text for transaction {transaction_id}.")
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
        logger.info(f"AI_TASK_SUCCESS: Successfully processed transaction {transaction_id}.")

    except Exception as e:
        # Catch any unexpected error and log it
        logger.error(f"AI_TASK_CRITICAL_FAIL: An unexpected error occurred for transaction {transaction_id}: {e}", exc_info=True)
        mongo.db.transactions.update_one(
            {"_id": ObjectId(transaction_id)},
            {"$set": {"status": "failed", "failure_reason": "An unexpected server error occurred."}}
        )