from flask import Blueprint, request, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from pydantic import ValidationError
from datetime import datetime, timezone
import redis
from bson import ObjectId

from app import mongo, bcrypt
from app.models.user import User
from .schemas import RegisterSchema, LoginSchema
from app.utils import success_response, error_response

auth_bp = Blueprint('auth_bp', __name__)

# The line "from app import token_blocklist" has been removed.

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = RegisterSchema(**request.get_json())
    except ValidationError as e:
        return error_response(e.errors(), 400)
    
    existing_user = mongo.db.users.find_one({"email": data.email.lower()})
    if existing_user:
        return error_response("A user with this email already exists.", 409)

    user_doc = User.create_user(data.email, data.password)
    mongo.db.users.insert_one(user_doc)
    
    return success_response({"message": "User registered successfully."}, 201)

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = LoginSchema(**request.get_json())
    except ValidationError as e:
        return error_response(e.errors(), 400)

    user = mongo.db.users.find_one({"email": data.email.lower()})
    if user and User.check_password(user['password'], data.password):
        user_id = str(user['_id'])
        access_token = create_access_token(identity=user_id, fresh=True)
        refresh_token = create_refresh_token(identity=user_id)
        return success_response({
            "access_token": access_token,
            "refresh_token": refresh_token
        })
    else:
        return error_response("Invalid credentials", 401)

# --- START OF FIX: Replaced the old logout function ---
@auth_bp.route('/logout', methods=['DELETE'])
@jwt_required(verify_type=False) 
def logout():
    """
    Revokes the current user's token by adding its JTI to the Redis blocklist.
    """
    token = get_jwt()
    jti = token["jti"]
    token_type = token["type"]
    
    exp_timestamp = token["exp"]
    now = datetime.now(timezone.utc)
    time_to_live = round(exp_timestamp - now.timestamp())

    try:
        redis_conn = redis.from_url(current_app.config['BROKER_URL'])
        
        if time_to_live > 0:
            redis_conn.setex(f"jti:{jti}", time_to_live, "blocked")

        return success_response({"message": f"{token_type.capitalize()} token successfully revoked."})
        
    except Exception as e:
        current_app.logger.error(f"Redis connection error on logout: {e}")
        return error_response("Could not revoke token due to a server issue.", 500)
# --- END OF FIX ---

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user_id, fresh=False)
    return success_response({"access_token": new_access_token})

@auth_bp.route('/profile', methods=['GET', 'POST'])
@jwt_required()
def profile():
    current_user_id = get_jwt_identity()
    user_object_id = ObjectId(current_user_id)

    if request.method == 'POST':
        data = request.get_json()
        income = data.get('income')
        if income is None:
            return error_response("Income is a required field.", 400)
        try:
            income = float(income)
            if income < 0: raise ValueError
        except (ValueError, TypeError):
            return error_response("Income must be a valid positive number.", 400)
        mongo.db.users.update_one({"_id": user_object_id}, {"$set": {"income": income}})
        updated_user = mongo.db.users.find_one({"_id": user_object_id})
        updated_user['_id'] = str(updated_user['_id'])
        return success_response(updated_user)

    user = mongo.db.users.find_one({"_id": user_object_id}, {"password": 0})
    if user:
        user['_id'] = str(user['_id'])
        if 'income' not in user:
            user['income'] = 0
        return success_response(user)
    else:
        return error_response("User not found", 404)