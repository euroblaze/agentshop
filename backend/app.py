from flask import Flask
from flask_cors import CORS
from .orm.base_model import db_manager
from .api.llm_endpoints import llm_bp
from .api.llm_chat_endpoints import llm_chat_bp
from .api.llm_analytics_endpoints import llm_analytics_bp
from .api.llm_config_endpoints import llm_config_bp
from .middleware.error_handler import setup_error_handling
import os


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', 'sqlite:///agentshop.db')
    
    # CORS configuration
    cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    CORS(app, origins=cors_origins)
    
    # Setup error handling
    setup_error_handling(app)
    
    # Register blueprints
    app.register_blueprint(llm_bp)
    app.register_blueprint(llm_chat_bp)
    app.register_blueprint(llm_analytics_bp)
    app.register_blueprint(llm_config_bp)
    
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