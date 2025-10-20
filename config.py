import os
from datetime import timedelta

# The `load_dotenv()` call has been removed.
# The container will now only use environment variables provided by Railway.

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