from flask import current_app
from app import celery
from app import mongo
from bson import ObjectId
from app.services.gemini_service import parse_expense_test, generate_spending_summary
from datetime import datetime, timedelta, timezone
from datetime import datetime, timedelta, timezone
IST = timezone(timedelta(hours=5, minutes=30))

@celery.task
def process_ai_transaction(transaction_id: str):
    """
    Celery task to process a transaction using the Gemini AI service.
    Logs the outcome of the operation.
    """
    logger = current_app.logger

    try:
        transaction = mongo.db.transactions.find_one({"_id": ObjectId(transaction_id)})
        if not transaction:
            logger.error(f"AI_TASK_FAIL: Transaction with ID {transaction_id} not found.")
            return

        raw_text = transaction.get("raw_text")
        if not raw_text:
            logger.error(f"AI_TASK_FAIL: Transaction {transaction_id} is missing raw_text for AI processing.")
            raise ValueError("Transaction is missing raw_text for AI processing.")

        logger.info(f"AI_TASK_START: Calling Gemini API for transaction {transaction_id}.")
        
        # ADDED: Try-catch to capture detailed Gemini errors (FIX #29)
        try:
            parsed_data = parse_expense_test(raw_text)
        except Exception as gemini_error:
            # ADDED: Store detailed Gemini error (FIX #29)
            error_message = str(gemini_error)
            logger.error(f"AI_TASK_GEMINI_ERROR: Gemini API failed for transaction {transaction_id}. Error: {error_message}")
            mongo.db.transactions.update_one(
                {"_id": ObjectId(transaction_id)},
                {"$set": {
                    "status": "failed",
                    "failure_reason": "AI parsing failed",
                    "error_details": error_message[:500]  # Store first 500 chars of error
                }}
            )
            return

        if not parsed_data:
            # ADDED: More specific error message (FIX #29)
            error_msg = "AI could not extract amount, category, or description from the text"
            mongo.db.transactions.update_one(
                {"_id": ObjectId(transaction_id)},
                {"$set": {
                    "status": "failed",
                    "failure_reason": error_msg,
                    "error_details": f"Input text: {raw_text[:100]}..."
                }}
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
        # ADDED: Capture and store unexpected errors with details (FIX #29)
        error_message = str(e)
        logger.error(f"AI_TASK_CRITICAL_FAIL: An unexpected error occurred for transaction {transaction_id}: {e}", exc_info=True)
        mongo.db.transactions.update_one(
            {"_id": ObjectId(transaction_id)},
            {"$set": {
                "status": "failed",
                "failure_reason": "Unexpected server error",
                "error_details": error_message[:500]
            }}
        )
        
@celery.task
def get_ai_summary_task(user_id_str: str):
    """
    Celery task to generate an AI spending summary for the last 30 days.
    """
    logger = current_app.logger
    user_id = ObjectId(user_id_str)
    
    logger.info(f"AI_SUMMARY_START: Starting summary generation for user {user_id_str}.")

    # Define the date range for the last 30 days
    end_date = datetime.now(IST)
    start_date = end_date - timedelta(days=30)

    # Aggregation pipeline to get spending by category
    pipeline = [
        {
            "$match": {
                "user_id": user_id,
                "status": "completed",
                "date": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            "$group": {
                "_id": "$category",
                "total": {"$sum": "$amount"}
            }
        },
        {
            "$project": {
                "category": "$_id",
                "total": 1,
                "_id": 0
            }
        },
        {"$sort": {"total": -1}}
    ]

    try:
        spending_data = list(mongo.db.transactions.aggregate(pipeline))
        
        if not spending_data:
            logger.warning(f"AI_SUMMARY_NODATA: No spending data found for user {user_id_str}.")
            return "You don't have any spending data from the last 30 days to analyze."

        summary = generate_spending_summary(spending_data)
        
        if summary:
            logger.info(f"AI_SUMMARY_SUCCESS: Successfully generated summary for user {user_id_str}.")
            return summary
        else:
            raise Exception("Gemini service failed to generate summary.")

    except Exception as e:
        logger.error(f"AI_SUMMARY_FAIL: Failed to generate summary for user {user_id_str}. Error: {e}")
        raise