#!/usr/bin/env python3
"""
Core Database Management

Provides unified database connection and session management for all AgentShop modules.
Combines the best features from both webshop and backend database implementations.
"""

import os
import logging
from typing import Optional, Any, Dict
from contextlib import contextmanager
from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.exc import SQLAlchemyError

from .base_model import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Enhanced database connection and session manager.
    
    Provides comprehensive database management with connection pooling,
    error handling, and configuration options suitable for all AgentShop modules.
    """
    
    def __init__(self, database_url: Optional[str] = None, **engine_kwargs):
        """
        Initialize database manager.
        
        Args:
            database_url: Database connection URL. If None, uses environment or default
            **engine_kwargs: Additional SQLAlchemy engine configuration
        """
        self.database_url = self._get_database_url(database_url)
        self.engine_kwargs = self._prepare_engine_kwargs(**engine_kwargs)
        self.engine = None
        self.SessionLocal = None
        
        self._initialize_engine()
        self._setup_event_listeners()
    
    def _get_database_url(self, database_url: Optional[str]) -> str:
        """Determine the database URL to use."""
        if database_url:
            return database_url
        
        # Check environment variable
        env_url = os.getenv('DATABASE_URL')
        if env_url:
            return env_url
        
        # Default to SQLite in project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        db_path = os.path.join(project_root, 'agentshop.db')
        return f"sqlite:///{db_path}"
    
    def _prepare_engine_kwargs(self, **kwargs) -> Dict[str, Any]:
        """Prepare SQLAlchemy engine configuration."""
        defaults = {
            'echo': os.getenv('SQL_DEBUG', 'false').lower() == 'true',
            'pool_pre_ping': True,
            'pool_recycle': 300,
        }
        
        # SQLite-specific optimizations
        if self.database_url.startswith('sqlite'):
            defaults.update({
                'poolclass': StaticPool,
                'connect_args': {
                    'check_same_thread': False,
                    'timeout': 30
                }
            })
        else:
            # PostgreSQL/MySQL optimizations
            defaults.update({
                'poolclass': QueuePool,
                'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),
                'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '20')),
                'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30')),
            })
        
        # Override defaults with provided kwargs
        defaults.update(kwargs)
        return defaults
    
    def _initialize_engine(self):
        """Initialize the SQLAlchemy engine and session factory."""
        try:
            self.engine = create_engine(self.database_url, **self.engine_kwargs)
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info(f"Database engine initialized: {self.database_url}")
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise
    
    def _setup_event_listeners(self):
        """Setup SQLAlchemy event listeners for enhanced functionality."""
        
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Enable SQLite optimizations when using SQLite."""
            if self.database_url.startswith('sqlite'):
                cursor = dbapi_connection.cursor()
                # Enable foreign key constraints
                cursor.execute("PRAGMA foreign_keys=ON")
                # Enable WAL mode for better concurrency
                cursor.execute("PRAGMA journal_mode=WAL")
                # Optimize SQLite performance
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA cache_size=10000")
                cursor.execute("PRAGMA temp_store=memory")
                cursor.close()
    
    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Returns:
            New SQLAlchemy session instance
        """
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized. Call create_tables() first.")
        
        return self.SessionLocal()
    
    def get_engine(self):
        """Get the SQLAlchemy engine."""
        return self.engine
    
    @contextmanager
    def session_scope(self):
        """
        Context manager for database sessions with automatic cleanup.
        
        Usage:
            with db_manager.session_scope() as session:
                # Use session here
                session.add(model_instance)
                # Automatic commit on success, rollback on exception
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_tables(self, checkfirst: bool = True):
        """
        Create all database tables.
        
        Args:
            checkfirst: Only create tables that don't already exist
        """
        try:
            Base.metadata.create_all(bind=self.engine, checkfirst=checkfirst)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def drop_tables(self, checkfirst: bool = True):
        """
        Drop all database tables.
        
        Args:
            checkfirst: Only drop tables that exist
            
        Warning:
            This will permanently delete all data. Use with extreme caution!
        """
        try:
            Base.metadata.drop_all(bind=self.engine, checkfirst=checkfirst)
            logger.warning("Database tables dropped")
        except SQLAlchemyError as e:
            logger.error(f"Failed to drop tables: {e}")
            raise
    
    def recreate_tables(self):
        """
        Drop and recreate all tables.
        
        Warning:
            This will permanently delete all data. Use with extreme caution!
        """
        logger.warning("Recreating all database tables - all data will be lost!")
        self.drop_tables()
        self.create_tables()
    
    def get_table_names(self) -> list:
        """Get list of all table names in the database."""
        metadata = MetaData()
        metadata.reflect(bind=self.engine)
        return list(metadata.tables.keys())
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a specific table exists."""
        return table_name in self.get_table_names()
    
    def execute_raw_sql(self, sql: str, parameters: Optional[Dict] = None):
        """
        Execute raw SQL statement.
        
        Args:
            sql: SQL statement to execute
            parameters: Optional parameters for the SQL statement
            
        Returns:
            Result of the SQL execution
        """
        with self.session_scope() as session:
            return session.execute(sql, parameters or {})
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the database connection.
        
        Returns:
            Dictionary with health check results
        """
        try:
            with self.session_scope() as session:
                # Simple query to test connection
                result = session.execute("SELECT 1")
                result.fetchone()
                
                return {
                    'status': 'healthy',
                    'database_url': self.database_url.split('@')[-1],  # Hide credentials
                    'engine_pool_size': getattr(self.engine.pool, 'size', None),
                    'engine_pool_checked_out': getattr(self.engine.pool, 'checkedout', None),
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'database_url': self.database_url.split('@')[-1],  # Hide credentials
            }
    
    def close(self):
        """Close the database engine and clean up resources."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database engine closed")


# Global database manager instance
db_manager = DatabaseManager()


def get_db_session() -> Session:
    """
    Get database session - use this in repositories and services.
    
    Returns:
        New SQLAlchemy session instance
    """
    return db_manager.get_session()


def get_db_engine():
    """Get the global database engine."""
    return db_manager.get_engine()


@contextmanager
def db_session():
    """
    Context manager for database sessions.
    
    Usage:
        with db_session() as session:
            # Use session here
    """
    with db_manager.session_scope() as session:
        yield session


def create_all_tables():
    """Create all database tables."""
    db_manager.create_tables()


def drop_all_tables():
    """Drop all database tables (use with caution!)."""
    db_manager.drop_tables()


def recreate_all_tables():
    """Recreate all database tables (use with extreme caution!)."""
    db_manager.recreate_tables()


def initialize_database(database_url: Optional[str] = None, **engine_kwargs):
    """
    Initialize the global database manager with custom settings.
    
    Args:
        database_url: Custom database URL
        **engine_kwargs: Additional engine configuration
    """
    global db_manager
    db_manager = DatabaseManager(database_url, **engine_kwargs)


def database_health_check() -> Dict[str, Any]:
    """Perform a health check on the database."""
    return db_manager.health_check()


# Database configuration presets for different environments
DATABASE_CONFIGS = {
    'development': {
        'echo': True,
        'pool_pre_ping': True,
    },
    'testing': {
        'echo': False,
        'pool_pre_ping': False,
        'strategy': 'mock',
    },
    'production': {
        'echo': False,
        'pool_pre_ping': True,
        'pool_size': 20,
        'max_overflow': 40,
        'pool_timeout': 60,
    }
}


def configure_for_environment(env: str = 'development'):
    """
    Configure database for a specific environment.
    
    Args:
        env: Environment name ('development', 'testing', 'production')
    """
    config = DATABASE_CONFIGS.get(env, DATABASE_CONFIGS['development'])
    initialize_database(**config)