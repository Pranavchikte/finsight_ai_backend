import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment-specific .env file
env = os.getenv('FLASK_ENV', 'development')
if env == 'production':
    load_dotenv('.env.production')
else:
    load_dotenv('.env.local')

class Config:
    MONGO_URI = os.environ.get('MONGO_URI')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    FRONTEND_URL = os.environ.get('FRONTEND_URL')
    
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ["access", "refresh"]
    
    BROKER_URL = os.environ.get('BROKER_URL')
    RESULT_BACKEND = os.environ.get('RESULT_BACKEND')
    BROKER_CONNECTION_RETRY_ON_STARTUP = True
    
    # Mail configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    