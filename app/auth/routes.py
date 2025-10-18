from flask import Blueprint, jsonify, request
from app import mongo
from app.models.user import User
import re
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from bson import ObjectId
from pydantic import ValidationError
from .schemas import RegisterSchema, LoginSchema


auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        # Pydantic validates the incoming JSON against our schema.
        # If it's invalid, it raises a ValidationError.
        data = RegisterSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Invalid data provided", "details": e.errors()}), 400
    except Exception:
        return jsonify({"error": "Request must be JSON"}), 400

    if mongo.db.users.find_one({"email": data.email.lower()}):
        return jsonify({"error": "User with this email already exists"}), 409

    user_doc = User.create_user(email=data.email, password=data.password)
    mongo.db.users.insert_one(user_doc)
    
    return jsonify({"message": "User registered successfully"}), 201
    
@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = LoginSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Invalid data provided", "details": e.errors()}), 400
    except Exception:
        return jsonify({"error": "Request must be JSON"}), 400

    user = mongo.db.users.find_one({"email": data.email.lower()})

    if user and User.check_password(user['password'], data.password):
        access_token = create_access_token(identity=str(user['_id']), expires_delta=False)
        return jsonify(access_token=access_token), 200
    
    return jsonify({"error": "Invalid email or password"}), 401


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
    
