from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import mongo
from app.models.transaction import Transaction
from bson import ObjectId
from bson.errors import InvalidId
from app.services.gemini_service import parse_expense_test
from app.models.transaction import PREDEFINED_CATEGORIES

transactions_bp = Blueprint('transactions_bp', __name__)

@transactions_bp.route('/', methods=['POST'])
@jwt_required()
def add_transactions():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'mode' not in data:
        return jsonify({"error": "Missing mode (manual or ai)"}), 400
    
    mode = data.get('mode')
    
    if mode == 'manual':
        required_fields = ['amount', 'category', 'description']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields for manual entry"}),400
        
        transactions_doc = Transaction.create_transaction(
            user_id=ObjectId(current_user_id),
            amount=data.get('amount'),
            category=data.get('category'),
            description=data.get('description'),
            date=data.get('date')
        )
        
        if transactions_doc is None:
            return jsonify({"error": "Invalid data provided (e.g., bad category or amount)"}), 400
        
        result = mongo.db.transactions.insert_one(transactions_doc)
        transactions_doc['_id'] = str(result.inserted_id)
        transactions_doc['user_id'] = str(transactions_doc['user_id'])
        
        return jsonify(transactions_doc), 201
    
    elif mode == 'ai':
        text = data.get('text')
        if not text:
            return jsonify({"error": "Missing 'text' for AI mode"}), 400
        
        parsed_data = parse_expense_test(text)
        
        if not parsed_data:
            return jsonify({"error": "AI could not parse the expense"}), 422
        
        transactions_doc = Transaction.create_transaction(
            user_id=ObjectId(current_user_id),
            amount=parsed_data.get('amount'),
            category=parsed_data.get('category'),
            description=parsed_data.get('description')
        )
        
        if transactions_doc is None:
            return jsonify({"error": "AI returned an invalid category"}), 422
        
        result = mongo.db.transactions.insert_one(transactions_doc)
        transactions_doc['_id'] = str(result.inserted_id)
        transactions_doc['user_id'] = str(transactions_doc['user_id'])
        
        return jsonify(transactions_doc), 201
    
    else:
        return jsonify({"error": "Invalid mode specified"}), 400
    
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
        return jsonify({"error": "Invvalid transactions ID format"}), 400
    
@transactions_bp.route('/categories', methods=['GET'])
def get_categories():
    
    return jsonify(list(PREDEFINED_CATEGORIES)), 200