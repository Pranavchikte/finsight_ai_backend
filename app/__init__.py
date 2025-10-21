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

# Initialize extensions globally, but without app context yet
mongo = PyMongo()
jwt = JWTManager()
bcrypt = Bcrypt()
celery = None

# --- FIX 1: Define the blocklist checker function WITHOUT the decorator ---
def check_if_token_in_blocklist(jwt_header, jwt_payload):
    """
    Callback function to check if a JWT has been revoked.
    Checks for the token's JTI in the Redis blocklist.
    """
    jti = jwt_payload["jti"]
    try:
        # Use Flask's current_app context proxy to access config safely
        redis_conn = redis.from_url(current_app.config['BROKER_URL'])
        token_is_blocked = redis_conn.get(f"jti:{jti}")
        return token_is_blocked is not None
    except Exception as e:
        # Log error but fail open (assume not blocked) if Redis fails
        current_app.logger.error(f"Redis connection error on token check: {e}")
        return False
# --- END FIX 1 ---

def create_app():
    global celery
    
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions WITH the app context
    mongo.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    celery = create_celery_app(app)

    # --- FIX 2: Register the blocklist loader AFTER jwt.init_app() ---
    jwt.token_in_blocklist_loader(check_if_token_in_blocklist)
    # --- END FIX 2 ---

    with app.app_context():
        # Import and configure blueprints
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
        
        # Register blueprints
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(transactions_bp, url_prefix='/api/transactions')
        app.register_blueprint(budgets_bp, url_prefix='/api/budgets')
        app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
        app.register_blueprint(ai_bp, url_prefix='/api/ai')
        
        # Create database indexes
        try:
            mongo.db.users.create_index("email", unique=True)
            mongo.db.transactions.create_index("user_id")
            mongo.db.transactions.create_index("date")
            mongo.db.budgets.create_index([("user_id", 1), ("month", 1), ("year", 1)])
        except Exception as e:
            app.logger.error(f"Error creating MongoDB indexes: {e}")
            # Depending on severity, you might want to raise the error
            # or handle it gracefully if indexes failing isn't critical at startup.

        # Basic routes
        @app.route('/', methods=['GET'])
        def index():
            return {"api_status": "FinSight AI Backend v2.0 is running"}, 200
        
        @app.route('/health', methods=['GET'])
        def health_check():
            try:
                # Check DB connection
                mongo.cx.admin.command('ping') 
                # Check Redis connection
                redis_conn = redis.from_url(app.config['BROKER_URL'])
                redis_conn.ping()
                return jsonify({"status": "healthy"}), 200
            except Exception as e:
                app.logger.error(f"Health check failed: {e}")
                return jsonify({"status": "unhealthy", "reason": str(e)}), 500
        
    # Logging configuration
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
        
    return app