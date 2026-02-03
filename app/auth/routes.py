from flask import Blueprint, request, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from pydantic import ValidationError
from datetime import datetime, timezone
import redis
from bson import ObjectId
import re # ADDED: For password validation
from app import mongo, bcrypt
from app.tasks.email_tasks import send_email_task
from app.models.user import User
from .schemas import RegisterSchema, LoginSchema
from app.utils import success_response, error_response, generate_reset_token, verify_reset_token

auth_bp = Blueprint('auth_bp', __name__)

# ADDED: Password strength validation helper (FIX #26)
def validate_password_strength(password):
    """
    Validates password meets security requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one number
    - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    
    return True, ""

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = RegisterSchema(**request.get_json())
    except ValidationError as e:
        return error_response(e.errors(), 400)
    
    # FIX #25: Email case normalization (already done with .lower())
    email_normalized = data.email.lower()
    
    # FIX #26: Password strength validation
    is_valid, error_msg = validate_password_strength(data.password)
    if not is_valid:
        return error_response(error_msg, 400)
    
    existing_user = mongo.db.users.find_one({"email": email_normalized})
    if existing_user:
        return error_response("A user with this email already exists.", 409)

    user_doc = User.create_user(email_normalized, data.password)
    mongo.db.users.insert_one(user_doc)
    
    return success_response({"message": "User registered successfully."}, 201)

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = LoginSchema(**request.get_json())
    except ValidationError as e:
        # ADDED: Check for rate limit error (FIX #28)
        error_list = e.errors()
        for err in error_list:
            if "rate limit" in str(err).lower() or "too many" in str(err).lower():
                return error_response("Too many login attempts. Please try again later.", 429)
        return error_response(error_list, 400)

    # FIX #25: Email case normalization (already done with .lower())
    email_normalized = data.email.lower()
    
    user = mongo.db.users.find_one({"email": email_normalized})
    if user and User.check_password(user['password'], data.password):
        user_id = str(user['_id'])
        access_token = create_access_token(identity=user_id, fresh=True)
        refresh_token = create_refresh_token(identity=user_id)
        return success_response({
            "access_token": access_token,
            "refresh_token": refresh_token
        })
    else:
        # FIX #30: Generic error message for brute force protection
        return error_response("Invalid email or password", 401)

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

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user_id, fresh=False)
    return success_response({"access_token": new_access_token})


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Sends a password reset email to the user.
    """
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return error_response("Email is required.", 400)
    
    # FIX #25: Email case normalization
    email = email.lower()
    user = mongo.db.users.find_one({"email": email})
    
    # Always return success to prevent email enumeration attacks
    if not user:
        return success_response({"message": "If an account exists with that email, a reset link has been sent."})
    
    # Generate reset token
    token = generate_reset_token(email)
    
    # Create reset link
    reset_link = f"{current_app.config['FRONTEND_URL']}/reset-password?token={token}"
    
    # Send email
    try:
        subject = "Reset Your FinSight AI Password"
        html_content = f"""
                        <html>
                            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                                    <h2 style="color: #2563eb;">Reset Your Password</h2>
                                    <p>You requested to reset your password for your FinSight AI account.</p>
                                    <p>Click the button below to reset your password:</p>
                                    <div style="text-align: center; margin: 30px 0;">
                                        <a href="{reset_link}" 
                                        style="background-color: #2563eb; color: white; padding: 12px 30px; 
                                                text-decoration: none; border-radius: 5px; display: inline-block;">
                                            Reset Password
                                        </a>
                                    </div>
                                    <p style="color: #666; font-size: 14px;">
                                        This link will expire in 1 hour for security reasons.
                                    </p>
                                    <p style="color: #666; font-size: 14px;">
                                        If you didn't request this, please ignore this email.
                                    </p>
                                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                                    <p style="color: #999; font-size: 12px;">
                                        FinSight AI - Intelligent Expense Tracking
                                    </p>
                                </div>
                            </body>
                        </html>
                        """

        send_email_task.delay(email, subject, html_content)
        current_app.logger.info(f"Password reset email sent to {email}")
    except Exception as e:
        current_app.logger.error(f"Failed to send reset email to {email}: {e}")
        return error_response("Failed to send reset email. Please try again later.", 500)
    
    return success_response({"message": "If an account exists with that email, a reset link has been sent."})


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Resets the user's password using a valid token.
    """
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('password')
    
    if not token or not new_password:
        return error_response("Token and new password are required.", 400)
    
    # FIX #26: Password strength validation for reset
    is_valid, error_msg = validate_password_strength(new_password)
    if not is_valid:
        return error_response(error_msg, 400)
    
    # Verify token
    email = verify_reset_token(token)
    if not email:
        return error_response("Invalid or expired reset token.", 400)
    
    # Find user and update password
    user = mongo.db.users.find_one({"email": email})
    if not user:
        return error_response("User not found.", 404)
    
    # Hash new password
    hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    
    # Update password in database
    mongo.db.users.update_one(
        {"email": email},
        {"$set": {"password": hashed_password}}
    )
    
    current_app.logger.info(f"Password successfully reset for {email}")
    return success_response({"message": "Password reset successful. You can now login with your new password."})


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
            if income < 0:
                return error_response("Income cannot be negative", 400)
            if income > 100000000:
                return error_response("Income too large. Maximum is ₹100,000,000", 400)
            income = round(income, 2)
        except (ValueError, TypeError):
            return error_response("Income must be a valid number", 400)
            
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