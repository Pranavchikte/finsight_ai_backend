import redis
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
from datetime import datetime, timezone
from flask import current_app
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
@jwt_required(verify_type=False) 
def logout():
    """
    Revokes the current user's token by adding its JTI to the Redis blocklist.
    The token will be blocked for its remaining lifetime.
    """
    token = get_jwt()
    jti = token["jti"]
    token_type = token["type"]
    
    # Calculate the remaining time until the token expires
    exp_timestamp = token["exp"]
    now = datetime.now(timezone.utc)
    time_to_live = round(exp_timestamp - now.timestamp())

    try:
        # Connect to Redis and add the token's JTI to the blocklist
        redis_conn = redis.from_url(current_app.config['BROKER_URL'])
        
        # Using setex to store the JTI with an expiration time (in seconds)
        # We only store it if it has a positive time to live
        if time_to_live > 0:
            redis_conn.setex(f"jti:{jti}", time_to_live, "blocked")

        return success_response({"message": f"{token_type.capitalize()} token successfully revoked."})
        
    except Exception as e:
        current_app.logger.error(f"Redis connection error on logout: {e}")
        return error_response("Could not revoke token due to a server issue.", 500)

@auth_bp.route('/profile', methods=['GET', 'POST'])
@jwt_required()
def profile():
    """
    GET: Fetches the current user's profile information.
    POST: Updates the current user's profile information (e.g., income).
    """
    current_user_id = get_jwt_identity()
    user_object_id = ObjectId(current_user_id)

    # --- HANDLE POST REQUEST TO UPDATE PROFILE ---
    if request.method == 'POST':
        data = request.get_json()
        income = data.get('income')

        if income is None:
            return error_response("Income is a required field.", 400)
        
        try:
            # Ensure income is a valid positive number
            income = float(income)
            if income < 0:
                raise ValueError
        except (ValueError, TypeError):
            return error_response("Income must be a valid positive number.", 400)

        mongo.db.users.update_one(
            {"_id": user_object_id},
            {"$set": {"income": income}}
        )
        
        updated_user = mongo.db.users.find_one({"_id": user_object_id})
        updated_user['_id'] = str(updated_user['_id']) # Convert ObjectId for JSON response
        
        return success_response(updated_user)

    # --- HANDLE GET REQUEST TO FETCH PROFILE ---
    user = mongo.db.users.find_one({"_id": user_object_id}, {"password": 0})
    if user:
        user['_id'] = str(user['_id'])
        # Ensure the income field exists, default to 0 if not set
        if 'income' not in user:
            user['income'] = 0
            
        return success_response(user)
    else:
        return error_response("User not found", 404)