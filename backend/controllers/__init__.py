#!/usr/bin/env python3
"""
Unified Controllers Package - All API controllers for AgentShop

Contains all controllers in a single location for simplified architecture:
- Base controller functionality from core
- LLM-related endpoints
- Webshop controllers (products, orders, customers, admin, auth)
"""

# Base controller from core
from core.api.base_controller import BaseController

# Webshop controllers
from .products_controller import products_bp
from .customers_controller import customers_bp
from .orders_controller import orders_bp
from .admin_controller import admin_bp
from .auth_controller import auth_bp

# LLM controllers (import blueprints if they exist)
try:
    from .llm_endpoints import llm_bp
    LLM_BLUEPRINTS = [llm_bp]
except ImportError:
    LLM_BLUEPRINTS = []

try:
    from .llm_chat_endpoints import llm_chat_bp
    LLM_BLUEPRINTS.append(llm_chat_bp)
except ImportError:
    pass

try:
    from .llm_config_endpoints import llm_config_bp
    LLM_BLUEPRINTS.append(llm_config_bp)
except ImportError:
    pass

try:
    from .llm_analytics_endpoints import llm_analytics_bp
    LLM_BLUEPRINTS.append(llm_analytics_bp)
except ImportError:
    pass

__all__ = [
    'BaseController',
    # Webshop blueprints
    'products_bp',
    'customers_bp', 
    'orders_bp',
    'admin_bp',
    'auth_bp',
    # LLM blueprints
    'LLM_BLUEPRINTS'
]