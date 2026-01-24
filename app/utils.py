from flask import jsonify, current_app
from itsdangerous import URLSafeTimedSerializer

def success_response(data, status_code=200):
  
    response = {
        "status": "success",
        "data": data
    }
    return jsonify(response), status_code

def error_response(message, status_code):
    
    status = "fail" if 400 <= status_code < 500 else "error"
    
    response_data_key = "details" if isinstance(message, dict) or isinstance(message, list) else "message"

    response = {
        "status": status,
        "data": {response_data_key: message}
    }
    return jsonify(response), status_code

def generate_reset_token(email):
    """
    Generates a secure, time-limited token for password reset.
    Token expires after 1 hour.
    """
    serializer = URLSafeTimedSerializer(current_app.config['JWT_SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset-salt')


def verify_reset_token(token, expiration=3600):
    """
    Verifies the password reset token.
    Returns the email if valid, None if expired/invalid.
    
    Args:
        token: The reset token to verify
        expiration: Token validity in seconds (default 1 hour = 3600s)
    """
    serializer = URLSafeTimedSerializer(current_app.config['JWT_SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
        return email
    except Exception:
        return None