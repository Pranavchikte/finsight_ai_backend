from app import bcrypt
from datetime import datetime, timedelta
import random
import string

class User:
    @staticmethod
    def create_user(email, password):
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        return{
            "email": email.lower(),
            "password": hashed_password,
            "created_at": datetime.utcnow()
        }
        
    @staticmethod
    def check_password(hashed_password, password):
        return bcrypt.check_password_hash(hashed_password, password)
    
    @staticmethod
    def generate_whatsapp_verification_code():
        return ''.join(random.choices(string.digits, k=6))
    
    @staticmethod
    def create_whatsapp_verification(user_id, whatsapp_number):
        code = User.generate_whatsapp_verification_code()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        return {
            "user_id": user_id,
            "whatsapp_number": whatsapp_number,
            "whatsapp_code": code,
            "whatsapp_code_expires": expires_at,
            "whatsapp_verified": False
        }
    
            