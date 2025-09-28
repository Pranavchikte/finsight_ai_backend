from flask import Blueprint, jsonify, request
from app import mongo
from app.models.user import User
import re
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from bson import ObjectId


auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
         return jsonify({"error": "Invalid email format"}), 400
    
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters long"}), 400
    
    if mongo.db.users.find_one({"email": email.lower()}):
        return jsonify({"error": "User with this email already exists"}), 409
    
    try:
        user_doc = User.create_user(email, password)
        mongo.db.users.insert_one(user_doc)
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    
    user_doc = mongo.db.users.find_one({"email": email.lower()})
    
    if not user_doc or not User.check_password(user_doc['password'], password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    identity = str(user_doc['_id'])
    expires = timedelta(hours=24)
    access_token = create_access_token(identity=identity, expires_delta=expires)
    
    return jsonify(access_token=access_token), 200


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    user = mongo.db.users.find_one({"_id": ObjectId(current_user_id)})

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "_id": str(user['_id']),
        "email": user['email']
    }), 200
    
