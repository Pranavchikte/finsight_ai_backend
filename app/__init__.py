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
cors = CORS()

celery = None

token_blocklist = set()

@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload):
    
    jti = jwt_payload["jti"]
    try:
        redis_conn = redis.from_url(current_app.config['BROKER_URL'])
        token_is_blocked = redis_conn.get(f"jti:{jti}")
        return token_is_blocked is not None
    except Exception as e:
        # If redis is down, we can log the error but should fail open
        # (i.e., assume token is not blocked) to avoid locking everyone out.
        # For higher security, you could fail closed (return True).
        current_app.logger.error(f"Redis connection error on token check: {e}")
        return False

def create_app():
    global celery
    
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # --- START LOGGING CONFIGURATION ---
    if not app.debug and not app.testing:
        # Create a logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Set up a rotating file handler
        file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
        
        # Set the log format
        log_format = '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Set the log level
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Finsight AI startup')
    # --- END LOGGING CONFIGURATION ---
    
    celery = create_celery_app(app)
    
    mongo.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, resources={r"/api/*":{"origins": app.config.get("FRONTEND_URL")}})
    
    with app.app_context():
        from .auth.routes import auth_bp
        from .transactions.routes import transactions_bp
        from .budgets.routes import budgets_bp 
        from .analytics.routes import analytics_bp 
        
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(transactions_bp, url_prefix='/api/transactions')
        app.register_blueprint(budgets_bp, url_prefix='/api/budgets')
        app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
        
        
        mongo.db.users.create_index("email", unique=True)
        mongo.db.transactions.create_index("user_id")
        mongo.db.transactions.create_index("date")
        mongo.db.budgets.create_index([("user_id", 1), ("month", 1), ("year", 1)])
        
        @app.route('/', methods=['GET'])
        def index():
            return {"api_status": "FinSight AI Backend v1.0 is running"}, 200
        
        @app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({"status": "healthy"}), 200
        
        return app