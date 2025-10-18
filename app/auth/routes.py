import json
from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token, 
    jwt_required, 
    get_jwt_identity,
    get_jwt
)
from bson import ObjectId
from pydantic import ValidationError

from app import mongo, token_blocklist # <-- Import the blocklist
from app.models.user import User
from .schemas import RegisterSchema, LoginSchema
from app.utils import success_response, error_response

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = RegisterSchema(**request.get_json())
    except ValidationError as e:
        error_details = json.loads(e.json())
        return error_response(error_details, 400)
    except Exception:
        return error_response("Request must be JSON", 400)

    if mongo.db.users.find_one({"email": data.email.lower()}):
        return error_response("User with this email already exists", 409)

    user_doc = User.create_user(email=data.email, password=data.password)
    mongo.db.users.insert_one(user_doc)
    
    return success_response({"message": "User registered successfully"}, 201)
    
@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = LoginSchema(**request.get_json())
    except ValidationError as e:
        error_details = json.loads(e.json())
        return error_response(error_details, 400)
    except Exception:
        return error_response("Request must be JSON", 400)

    user = mongo.db.users.find_one({"email": data.email.lower()})

    if user and User.check_password(user['password'], data.password):
        user_id = str(user['_id'])
        # Generate both an access and a refresh token
        access_token = create_access_token(identity=user_id)
        refresh_token = create_refresh_token(identity=user_id)
        
        return success_response({
            "access_token": access_token,
            "refresh_token": refresh_token
        })
    
    return error_response("Invalid email or password", 401)

# --- NEW ENDPOINT: REFRESH ---
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True) # This endpoint requires a valid REFRESH token
def refresh():
    current_user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user_id)
    return success_response({"access_token": new_access_token})

# --- NEW ENDPOINT: LOGOUT ---
@auth_bp.route('/logout', methods=['DELETE'])
@jwt_required() # Can be logged out with either an access or refresh token
def logout():
    jti = get_jwt()["jti"] # 'jti' is the unique identifier for a JWT
    token_blocklist.add(jti)
    return success_response({"message": "Successfully logged out"})

@auth_bp.route('/profile', methods=['GET'])
@jwt_required() # This requires a valid ACCESS token
def get_profile():
    current_user_id = get_jwt_identity()
    user = mongo.db.users.find_one({"_id": ObjectId(current_user_id)})

    if not user:
        return error_response("User not found", 404)

    user_data = {
        "_id": str(user['_id']),
        "email": user['email']
    }
    return success_response(user_data)