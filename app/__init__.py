import os
import redis
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, current_app
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from config import Config
from .celery_utils import create_celery_app

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
    
    # --- START OF FIX: MOVE LOGGING HERE ---
    # Logging configuration moved to the top
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
    
    # ---> YOUR VERIFICATION LINE <---
    app.logger.info(f"MONGO_URI loaded: {app.config.get('MONGO_URI')}")
    # --- END OF FIX ---

    # Initialize extensions
    mongo.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    celery = create_celery_app(app)

    with app.app_context():
        # Imports and blueprint registrations...
        from .auth.routes import auth_bp
        # ... (rest of your blueprint code)
        app.register_blueprint(ai_bp, url_prefix='/api/ai')
        
        # Create database indexes
        # This line will still cause a crash, but NOW it will be logged.
        mongo.db.users.create_index("email", unique=True)
        mongo.db.transactions.create_index("user_id")
        mongo.db.transactions.create_index("date")
        mongo.db.budgets.create_index([("user_id", 1), ("month", 1), ("year", 1)])
        
        @app.route('/', methods=['GET'])
        def index():
            return {"api_status": "FinSight AI Backend v2.0 is running"}, 200
        
        @app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({"status": "healthy"}), 200
            
    return app