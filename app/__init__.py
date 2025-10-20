# In app/app/__init__.py

import os
import redis
import logging
import time # <-- Keep this import
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, current_app
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from config import Config
from .celery_utils import create_celery_app
# No need for ConnectionFailure import anymore

# (The rest of your initializations remain the same)
mongo = PyMongo()
jwt = JWTManager()
bcrypt = Bcrypt()
celery = None

@jwt.token_in_blocklist_loader
# ... (this function remains the same)

def create_app():
    global celery
    
    app = Flask(__name__)
    app.config.from_object(Config)

    # Logger setup (keep at the top)
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
    
    # Initialize extensions
    mongo.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    celery = create_celery_app(app)

    with app.app_context():
        # Import and register blueprints
        from .auth.routes import auth_bp
        from .transactions.routes import transactions_bp
        from .budgets.routes import budgets_bp 
        from .analytics.routes import analytics_bp 
        from .ai.routes import ai_bp
        
        frontend_url = app.config.get("FRONTEND_URL")
        CORS(auth_bp, origins=frontend_url)
        CORS(transactions_bp, origins=frontend_url)
        CORS(budgets_bp, origins=frontend_url)
        CORS(analytics_bp, origins=frontend_url)
        CORS(ai_bp, origins=frontend_url)
        
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(transactions_bp, url_prefix='/api/transactions')
        app.register_blueprint(budgets_bp, url_prefix='/api/budgets')
        app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
        app.register_blueprint(ai_bp, url_prefix='/api/ai')
        
        # --- FINAL FIX: CATCH THE CORRECT ERROR ---
        max_retries = 5
        retry_delay = 5  # Increased delay to 5 seconds for cloud environments
        for attempt in range(max_retries):
            try:
                app.logger.info(f"Attempting to create DB indexes (Attempt {attempt + 1}/{max_retries})")
                # This is the line that will fail if the DB is not ready
                mongo.db.users.create_index("email", unique=True)
                mongo.db.transactions.create_index("user_id")
                mongo.db.transactions.create_index("date")
                mongo.db.budgets.create_index([("user_id", 1), ("month", 1), ("year", 1)])
                app.logger.info("Database indexes created successfully.")
                break  # Success, exit the loop
            except AttributeError as e: # Catch the actual error that occurs
                app.logger.error(f"Failed to create indexes on attempt {attempt + 1}: {e}. DB likely not ready.")
                if attempt < max_retries - 1:
                    app.logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    app.logger.error("Could not connect to the database. Aborting startup.")
                    raise  # Re-raise the exception to stop the app
        # --- END OF FINAL FIX ---

        @app.route('/', methods=['GET'])
        def index():
            return {"api_status": "FinSight AI Backend v2.0 is running"}, 200
        
        @app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({"status": "healthy"}), 200
            
    return app