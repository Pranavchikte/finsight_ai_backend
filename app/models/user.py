from app import bcrypt
from datetime import datetime

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
    
            