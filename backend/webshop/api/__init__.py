#!/usr/bin/env python3
"""
AgentShop WebShop API Package
Provides REST API endpoints for the AgentShop webshop functionality
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import os

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)

def create_app(config_name='development'):
    """
    Application factory pattern for Flask app creation
    
    Args:
        config_name: Configuration name (development, testing, production)
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(get_config_object(config_name))
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    
    # Enable CORS for frontend integration
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['http://localhost:3000']))
    
    # Configure logging
    configure_logging(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register CLI commands
    register_cli_commands(app)
    
    return app

def get_config_object(config_name):
    """Get configuration object based on environment"""
    config_objects = {
        'development': 'config.DevelopmentConfig',
        'testing': 'config.TestingConfig', 
        'production': 'config.ProductionConfig'
    }
    
    return config_objects.get(config_name, 'config.DevelopmentConfig')

def configure_logging(app):
    """Configure application logging"""
    if not app.debug:
        # Production logging setup
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(name)s %(message)s'
        )
    else:
        # Development logging setup
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s %(name)s %(message)s'
        )

def register_blueprints(app):
    """Register API blueprints"""
    from .controllers.products_controller import products_bp
    from .controllers.customers_controller import customers_bp  
    from .controllers.orders_controller import orders_bp
    from .controllers.admin_controller import admin_bp
    from .controllers.auth_controller import auth_bp
    
    # Register blueprints with URL prefixes
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(customers_bp, url_prefix='/api/customers')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

def register_error_handlers(app):
    """Register global error handlers"""
    from .utils.error_handlers import register_error_handlers as reg_handlers
    reg_handlers(app)

def register_cli_commands(app):
    """Register CLI commands"""
    from .cli_commands import register_commands
    register_commands(app)