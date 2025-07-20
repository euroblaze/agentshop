from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from .orm.base_model import db_manager
from .api.llm_endpoints import llm_bp
from .api.llm_chat_endpoints import llm_chat_bp
from .api.llm_analytics_endpoints import llm_analytics_bp
from .api.llm_config_endpoints import llm_config_bp
from .middleware.error_handler import setup_error_handling
import os

# Import security components
try:
    from .middleware.security_middleware import SecurityMiddleware
    from .security.auth_security import SecurityHeaders
    import redis
    SECURITY_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Security components not available: {e}")
    SECURITY_AVAILABLE = False

# Import webshop blueprints
try:
    from .controllers.auth_controller import auth_bp
    from .controllers.admin_controller import admin_bp
    from .controllers.customers_controller import customers_bp
    from .controllers.products_controller import products_bp
    from .controllers.orders_controller import orders_bp
    from .controllers.cart_controller import cart_bp
    WEBSHOP_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Webshop controllers not available: {e}")
    WEBSHOP_AVAILABLE = False


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', 'sqlite:///agentshop.db')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config['SECRET_KEY'])
    # JWT Security Configuration
    from datetime import timedelta
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)  # 1 hour expiry
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=7)  # 7 days for refresh
    app.config['REDIS_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # CORS configuration
    cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    CORS(app, origins=cors_origins)
    
    # Initialize JWT
    jwt = JWTManager(app)
    
    # Initialize security middleware
    if SECURITY_AVAILABLE:
        try:
            redis_client = redis.Redis.from_url(app.config['REDIS_URL'])
            security_middleware = SecurityMiddleware(app, redis_client)
            print("Security middleware initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize security middleware: {e}")
    
    # Setup error handling
    setup_error_handling(app)
    
    # Register blueprints
    app.register_blueprint(llm_bp)
    app.register_blueprint(llm_chat_bp)
    app.register_blueprint(llm_analytics_bp)
    app.register_blueprint(llm_config_bp)
    
    # Register webshop blueprints if available
    if WEBSHOP_AVAILABLE:
        app.register_blueprint(auth_bp)
        app.register_blueprint(admin_bp)
        app.register_blueprint(customers_bp)
        app.register_blueprint(products_bp)
        app.register_blueprint(orders_bp)
        app.register_blueprint(cart_bp)
        print("Webshop blueprints registered successfully")
    else:
        print("Webshop functionality not available")
    
    # Create database tables
    with app.app_context():
        try:
            db_manager.create_tables()
            print("Database tables created successfully")
        except Exception as e:
            print(f"Error creating database tables: {e}")
    
    @app.route('/health')
    def health_check():
        """Basic health check endpoint"""
        return {"status": "healthy", "service": "agentshop-backend"}
    
    @app.route('/')
    def index():
        """Root endpoint"""
        return {
            "message": "AgentShop Backend API", 
            "version": "1.0.0",
            "endpoints": {
                "llm": "/api/llm",
                "chat": "/api/llm/chat", 
                "analytics": "/api/llm/analytics",
                "config": "/api/llm/config"
            }
        }
    
    return app


if __name__ == '__main__':
    app = create_app()
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)