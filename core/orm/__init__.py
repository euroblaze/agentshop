"""
Core ORM Module

Provides unified database models and connection management for all AgentShop modules.
Combines the best features from the webshop and backend ORM implementations.
"""

from .base_model import BaseModel, Base, TimestampMixin, SoftDeleteMixin
from .database import DatabaseManager, get_db_session, create_all_tables, drop_all_tables

__all__ = [
    'BaseModel',
    'Base', 
    'TimestampMixin',
    'SoftDeleteMixin',
    'DatabaseManager',
    'get_db_session',
    'create_all_tables',
    'drop_all_tables'
]