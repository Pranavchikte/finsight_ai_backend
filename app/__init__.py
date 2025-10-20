# In app/app/__init__.py

import os
import redis
import logging
import time # <-- Add this import
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, current_app
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from config import Config
from .celery_utils import create_celery_app
from pymongo.errors import ConnectionFailure # <-- And this import

mongo = PyMongo()
jwt = JWTManager()
bcrypt = Bcrypt()
celery = None

@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    try:
        redis_conn = redis.from_url(current_app.config['BROKER_URL'])
        token_is_blocked = redis_conn.get(f"jti:{jti}")
        return token_is_blocked is not None
    except Exception as e:
        current_app.logger.error(f"Redis connection error on token check: {e}")
        return False

def create_app():
    global celery
    
    app = Flask(__name__)
    app.config.from_object(Config)

    # --- START OF FIX 1: LOGGER INITIALIZED FIRST ---
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
        log_format = '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        file_handler.setFormatter(logging.Formatter(log_format))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Finsight AI startup')

    app.logger.info(f"MONGO_URI loaded: {app.config.get('MONGO_URI')}")
    # --- END OF FIX 1 ---
    
    # Initialize extensions
    mongo.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    celery = create_celery_app(app)

    with app.app_context():
        # --- START OF FIX 2: BLUEPRINT SCOPE CORRECTED ---
        # 1. Import all blueprints
        from .auth.routes import auth_bp
        from .transactions.routes import transactions_bp
        from .budgets.routes import budgets_bp 
        from .analytics.routes import analytics_bp 
        from .ai.routes import ai_bp
        
        # 2. Apply CORS
        frontend_url = app.config.get("FRONTEND_URL")
        CORS(auth_bp, origins=frontend_url)
        CORS(transactions_bp, origins=frontend_url)
        CORS(budgets_bp, origins=frontend_url)
        CORS(analytics_bp, origins=frontend_url)
        CORS(ai_bp, origins=frontend_url)
        
        # 3. Register blueprints
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(transactions_bp, url_prefix='/api/transactions')
        app.register_blueprint(budgets_bp, url_prefix='/api/budgets')
        app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
        app.register_blueprint(ai_bp, url_prefix='/api/ai')
        # --- END OF FIX 2 ---
        
        # --- START OF FIX 3: DATABASE CONNECTION RETRY LOGIC ---
        # Try to connect to the database and create indexes, with retries.
        max_retries = 5
        retry_delay = 3  # seconds
        for attempt in range(max_retries):
            try:
                app.logger.info(f"Attempting to connect to DB and create indexes (Attempt {attempt + 1}/{max_retries})")
                mongo.db.users.create_index("email", unique=True)
                mongo.db.transactions.create_index("user_id")
                mongo.db.transactions.create_index("date")
                mongo.db.budgets.create_index([("user_id", 1), ("month", 1), ("year", 1)])
                app.logger.info("Database indexes created successfully.")
                break  # Exit the loop if successful
            except ConnectionFailure as e:
                app.logger.error(f"DB connection failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    app.logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    app.logger.error("Could not connect to the database after several retries. App will fail to start.")
                    raise  # Re-raise the exception to cause the app to fail
        # --- END OF FIX 3 ---

        @app.route('/', methods=['GET'])
        def index():
            return {"api_status": "FinSight AI Backend v2.0 is running"}, 200
        
        @app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({"status": "healthy"}), 200
            
    return app