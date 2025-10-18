from flask import Flask, jsonify
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

def create_app():
    global celery
    
    app = Flask(__name__)
    app.config.from_object(Config)
    
    celery = create_celery_app(app)
    
    mongo.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, resources={r"/api/*":{"origins": app.config.get("FRONTEND_URL")}})
    
    with app.app_context():
        from .auth.routes import auth_bp
        from .transactions.routes import transactions_bp
        
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(transactions_bp, url_prefix='/api/transactions')
        
        mongo.db.users.create_index("email", unique=True)
        mongo.db.transactions.create_index("user_id")
        mongo.db.transactions.create_index("date")
        
        @app.route('/', methods=['GET'])
        def index():
            return {"api_status": "FinSight AI Backend v1.0 is running"}, 200
        
        @app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({"status": "healthy"}), 200
        
        return app