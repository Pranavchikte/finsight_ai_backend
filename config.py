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
    
    BROKER_URL = os.environ.get('BROKER_URL')
    RESULT_BACKEND = os.environ.get('RESULT_BACKEND')
    BROKER_CONNECTION_RETRY_ON_STARTUP = True
    
    # SendGrid Email (HTTP API)
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    FROM_EMAIL = os.environ.get('FROM_EMAIL')

    # Twilio WhatsApp
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    
    # Cron secret for scheduled tasks
    CRON_SECRET = os.environ.get('CRON_SECRET', 'your-secret-key')


    # API timeout configuration
    API_TIMEOUT = 30
    
    # Timezone configuration - store all dates in UTC
    DEFAULT_TIMEZONE = 'UTC'