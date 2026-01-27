import json
import re
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from bson.errors import InvalidId
from pydantic import ValidationError
from datetime import timezone, datetime
from app import mongo
from app.models.transaction import Transaction
from .schemas import AddTransactionSchema, PREDEFINED_CATEGORIES
from .tasks import process_ai_transaction
from app.utils import success_response, error_response # <-- Import our new helpers

transactions_bp = Blueprint('transactions_bp', __name__)

@transactions_bp.route('/', methods=['POST'])
@jwt_required()
def add_transactions():
    current_user_id = get_jwt_identity()
    
    try:
        data = AddTransactionSchema(**request.get_json())
    except ValidationError as e:
        error_details = json.loads(e.json())
        return error_response(error_details, 400)
    except Exception:
        return error_response("Request must be JSON", 400)
    
    # FIX #1: Amount Validation (Manual Mode)
    if data.mode == 'manual':
        if data.amount <= 0:
            return error_response("Amount must be greater than zero", 400)
        if data.amount > 10000000:  # 1 crore max
            return error_response("Amount too large. Maximum is ₹10,000,000", 400)
        # Round to 2 decimal places
        data.amount = round(data.amount, 2)

    # FIX #2: AI Text Validation
    if data.mode == 'ai':
        if not data.text or len(data.text.strip()) == 0:
            return error_response("AI description cannot be empty", 400)
        if len(data.text) > 200:
            return error_response("Description too long. Maximum 200 characters", 400)
        # Trim whitespace
        data.text = data.text.strip()

    transaction_doc = None
    if data.mode == 'manual':
        transaction_doc = Transaction.create_transaction(
            user_id=ObjectId(current_user_id),
            amount=data.amount,
            category=data.category,
            description=data.description
        )
    elif data.mode == 'ai':
        transaction_doc = Transaction.create_ai_transaction(
            user_id=ObjectId(current_user_id),
            text=data.text
        )

    result = mongo.db.transactions.insert_one(transaction_doc)
    inserted_id = result.inserted_id

    if data.mode == 'ai':
        process_ai_transaction.delay(str(inserted_id))

    final_doc = mongo.db.transactions.find_one({"_id": inserted_id})
    # Convert MongoDB specific types to strings for JSON response
    final_doc['_id'] = str(final_doc['_id'])
    final_doc['user_id'] = str(final_doc['user_id'])
    final_doc['date'] = final_doc['date'].isoformat()
    
    status_code = 201 if data.mode == 'manual' else 202
    return success_response(final_doc, status_code)

    
@transactions_bp.route('/', methods=['GET'])
@jwt_required()
def get_transactions():
    current_user_id = get_jwt_identity()
    
    # Get filter parameters
    search_query = request.args.get('search')
    category_filter = request.args.get('category')
    min_amount = request.args.get('min_amount')
    max_amount = request.args.get('max_amount')
    sort_by = request.args.get('sort_by', 'date')
    sort_order = request.args.get('sort_order', 'desc')

    # Build query
    query = {"user_id": ObjectId(current_user_id)}

    if search_query:
        query["description"] = {"$regex": re.compile(search_query, re.IGNORECASE)}

    if category_filter:
        query["category"] = category_filter
    
    # Add amount filtering
    if min_amount or max_amount:
        amount_filter = {}
        if min_amount:
            try:
                amount_filter["$gte"] = float(min_amount)
            except ValueError:
                return error_response("Invalid min_amount format", 400)
        if max_amount:
            try:
                amount_filter["$lte"] = float(max_amount)
            except ValueError:
                return error_response("Invalid max_amount format", 400)
        if amount_filter:
            query["amount"] = amount_filter
    
    # Sorting
    sort_direction = -1 if sort_order == 'desc' else 1
    sort_field = sort_by if sort_by in ['date', 'amount'] else 'date'
    
    # FIX #15: Add pagination
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 50, type=int)
    skip = (page - 1) * limit
    limit = min(limit, 100)

    total_count = mongo.db.transactions.count_documents(query)
    transactions_cursor = mongo.db.transactions.find(query).sort(sort_field, sort_direction).skip(skip).limit(limit)
    
    transactions_list = []
    for transaction in transactions_cursor:
        transaction['_id'] = str(transaction['_id'])
        transaction['user_id'] = str(transaction['user_id'])
        transaction['date'] = transaction['date'].isoformat()
        transactions_list.append(transaction)
        
    # FIX #15: Return pagination metadata
    return success_response({
        "transactions": transactions_list,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": (total_count + limit - 1) // limit
        }
    })

@transactions_bp.route('/<string:transaction_id>', methods=['GET'])
@jwt_required()
def get_transaction(transaction_id):
    current_user_id = get_jwt_identity()
    try:
        transaction = mongo.db.transactions.find_one({
            "_id": ObjectId(transaction_id),
            "user_id": ObjectId(current_user_id)
        })
        if transaction:
            transaction['_id'] = str(transaction['_id'])
            transaction['user_id'] = str(transaction['user_id'])
            transaction['date'] = transaction['date'].isoformat()
            return success_response(transaction)
        else:
            return error_response("Transaction not found", 404)
    except InvalidId:
        return error_response("Invalid transaction ID format", 400)

@transactions_bp.route('/<string:transaction_id>', methods=['DELETE'])
@jwt_required()
def delete_transaction(transaction_id):
    current_user_id = get_jwt_identity()
    
    try:
        delete_query = {
            "_id": ObjectId(transaction_id),
            "user_id": ObjectId(current_user_id)
        }
        result = mongo.db.transactions.find_one_and_delete(delete_query)
        
        if result:
            return success_response({"message": "Transaction deleted successfully"})
        else:
            return error_response("Transaction not found", 404)
        
    except InvalidId:
        return error_response("Invalid transaction ID format", 400)
    
    
@transactions_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_transaction_summary():
    current_user_id = get_jwt_identity()
    user_object_id = ObjectId(current_user_id)

    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    pipeline = [
        {
            "$match": {
                "user_id": user_object_id,
                "date": {"$gte": start_of_month},
                "status": "completed" # FIX #14: Only count completed
            }
        },
        {
            "$group": {
                "_id": None,
                "total_spend": {"$sum": "$amount"}
            }
        }
    ]

    result = list(mongo.db.transactions.aggregate(pipeline))

    if result:
        total_spend = result[0]['total_spend']
    else:
        total_spend = 0
        
    summary = {
        "current_month_spend": total_spend
    }
    
    return success_response(summary)
    
    
@transactions_bp.route('/<string:transaction_id>/status', methods=['GET'])
@jwt_required()
def get_transaction_status(transaction_id):
    current_user_id = get_jwt_identity()
    
    try:
        transaction = mongo.db.transactions.find_one(
            {"_id": ObjectId(transaction_id), "user_id": ObjectId(current_user_id)},
            {"status": 1} 
        )
        
        if transaction:
            return success_response({"status": transaction.get("status", "unknown")})
        else:
            return error_response("Transaction not found", 404)
            
    except InvalidId:
        return error_response("Invalid transaction ID format", 400)


@transactions_bp.route('/history', methods=['GET'])
@jwt_required()
def get_transaction_history():
    current_user_id = get_jwt_identity()
    user_object_id = ObjectId(current_user_id)
    
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    match_query = {
        "user_id": user_object_id,
        "status": "completed"
    }
    
    if start_date_str or end_date_str:
        date_filter = {}
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str).replace(tzinfo=timezone.utc)
                date_filter["$gte"] = start_date
            except ValueError:
                return error_response("Invalid start_date format. Use ISO 8601.", 400)
        
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str).replace(tzinfo=timezone.utc)
                date_filter["$lte"] = end_date
            except ValueError:
                return error_response("Invalid end_date format. Use ISO 8601.", 400)
        
        if date_filter:
            match_query["date"] = date_filter
    
    pipeline = [
        {"$match": match_query},
        {"$sort": {"date": -1}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$date"
                    }
                },
                "total_spend": {"$sum": "$amount"},
                "transaction_count": {"$sum": 1},
                "transactions": {
                    "$push": {
                        "_id": {"$toString": "$_id"},
                        "amount": "$amount",
                        "category": "$category",
                        "description": "$description",
                        "date": "$date"
                    }
                }
            }
        },
        {
            "$project": {
                "date": "$_id",
                "total_spend": 1,
                "transaction_count": 1,
                "transactions": 1,
                "_id": 0
            }
        },
        {"$sort": {"date": -1}}
    ]
    
    result = list(mongo.db.transactions.aggregate(pipeline))
    
    for day_group in result:
        for transaction in day_group["transactions"]:
            transaction["date"] = transaction["date"].isoformat()
    
    return success_response(result)

    
@transactions_bp.route('/categories', methods=['GET'])
def get_categories():
    return success_response(list(PREDEFINED_CATEGORIES))