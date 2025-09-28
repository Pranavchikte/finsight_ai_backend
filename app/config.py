import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.environ.get('MONGO_URI')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    FRONTEND_URL = os.environ.get('FRONTEND_URL')