import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import mongo
from app.models.transaction import Transaction
from bson import ObjectId
from bson.errors import InvalidId
from pydantic import ValidationError
from .schemas import AddTransactionSchema, PREDEFINED_CATEGORIES
from .tasks import process_ai_transaction

transactions_bp = Blueprint('transactions_bp', __name__)

@transactions_bp.route('/', methods=['POST'])
@jwt_required()
def add_transactions():
    current_user_id = get_jwt_identity()
    
    try:
        data = AddTransactionSchema(**request.get_json())
    except ValidationError as e:
        # This line is the fix. e.json() returns a JSON string,
        # and json.loads() converts it into a clean Python dictionary
        # that jsonify() can handle safely.
        error_details = json.loads(e.json())
        return jsonify({"error": "Invalid data provided", "details": error_details}), 400

    transaction_doc = None
    if data.mode == 'manual':
        # This is the corrected line
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
    final_doc['_id'] = str(final_doc['_id'])
    final_doc['user_id'] = str(final_doc['user_id'])
    final_doc['date'] = final_doc['date'].isoformat()
    
    status_code = 201 if data.mode == 'manual' else 202
    return jsonify(final_doc), status_code

    
@transactions_bp.route('/', methods=['GET'])
@jwt_required()
def get_transactions():
    current_user_id = get_jwt_identity()
    
    transactions_cursor = mongo.db.transactions.find({
        "user_id": ObjectId(current_user_id)
    }).sort("date", -1)
    
    transactions_list = []
    for transaction in transactions_cursor:
        transaction['_id'] = str(transaction['_id'])
        transaction['user_id'] = str(transaction['user_id'])
        transaction['date'] = transaction['date'].isoformat()
        transactions_list.append(transaction)
        
    return jsonify(transactions_list), 200


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
            return jsonify(transaction), 200
        else:
            return jsonify({"error": "Transaction not found"}), 404
    except InvalidId:
        return jsonify({"error": "Invalid transaction ID format"}), 400

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
            return jsonify({"message": "Transaction deleted successfully"}), 200
        else:
            return jsonify({"error": "Transaction not found"}), 404
        
    except InvalidId:
        return jsonify({"error": "Invalid transaction ID format"}), 400
    
    
@transactions_bp.route('/<string:transaction_id>/status', methods=['GET'])
@jwt_required()
def get_transaction_status(transaction_id):
    current_user_id = get_jwt_identity()
    
    try:
        transaction = mongo.db.transactions.find_one(
            {
                "_id": ObjectId(transaction_id), 
                "user_id": ObjectId(current_user_id)
            },
            {"status": 1} 
        )
        
        if transaction:
            return jsonify({"status": transaction.get("status", "unknown")}), 200
        else:
            return jsonify({"error": "Transaction not found"}), 404
            
    except InvalidId:
        return jsonify({"error": "Invalid transaction ID format"}), 400

    
@transactions_bp.route('/categories', methods=['GET'])
def get_categories():
    return jsonify(list(PREDEFINED_CATEGORIES)), 200