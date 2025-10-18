import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.environ.get('MONGO_URI')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    FRONTEND_URL = os.environ.get('FRONTEND_URL')
    
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ["access", "refresh"]
    
    
    broker_url = os.environ.get('BROKER_URL', 'redis://redis:6379/0')
    result_backend = os.environ.get('RESULT_BACKEND', 'redis://redis:6379/0')
    broker_connection_retry_on_startup = True
