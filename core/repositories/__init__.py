"""
Core Repository Module

Provides unified repository patterns and data access layer for all AgentShop modules.
Combines the best features from the webshop and backend repository implementations.
"""

from .base_repository import BaseRepository, RepositoryError
from .unit_of_work import UnitOfWork
from .query_builder import QueryBuilder, FilterExpression

__all__ = [
    'BaseRepository',
    'RepositoryError', 
    'UnitOfWork',
    'QueryBuilder',
    'FilterExpression'
]