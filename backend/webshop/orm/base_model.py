#!/usr/bin/env python3
"""
Base ORM Model - Abstract base class for all database models
Provides common fields and functionality for all entities
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List
import json
from sqlalchemy import Column, Integer, DateTime, String, create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
import os

# Create base class for all models
Base = declarative_base()


class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self, database_url: str = None):
        if database_url is None:
            # Default to SQLite database in project root
            db_path = os.path.join(
                os.path.dirname(__file__), '..', '..', '..', 'agentshop.db'
            )
            database_url = f"sqlite:///{db_path}"
        
        self.engine = create_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True,
            pool_recycle=300
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Create all tables
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        Base.metadata.drop_all(bind=self.engine)


class BaseModel(Base, ABC):
    """Abstract base model class with common fields and methods"""
    
    __abstract__ = True
    
    # Common fields for all models
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    @declared_attr
    def __tablename__(cls):
        """Generate table name from class name"""
        # Convert CamelCase to snake_case
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
    
    def to_dict(self, exclude_fields: List[str] = None) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        exclude_fields = exclude_fields or []
        result = {}
        
        for column in self.__table__.columns:
            field_name = column.name
            if field_name not in exclude_fields:
                value = getattr(self, field_name)
                
                # Handle datetime serialization
                if isinstance(value, datetime):
                    result[field_name] = value.isoformat()
                else:
                    result[field_name] = value
        
        return result
    
    def from_dict(self, data: Dict[str, Any], exclude_fields: List[str] = None) -> 'BaseModel':
        """Update model instance from dictionary"""
        exclude_fields = exclude_fields or ['id', 'created_at', 'updated_at']
        
        for key, value in data.items():
            if key not in exclude_fields and hasattr(self, key):
                setattr(self, key, value)
        
        return self
    
    def to_json(self, exclude_fields: List[str] = None) -> str:
        """Convert model instance to JSON string"""
        return json.dumps(self.to_dict(exclude_fields), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str, exclude_fields: List[str] = None) -> 'BaseModel':
        """Create model instance from JSON string"""
        data = json.loads(json_str)
        instance = cls()
        return instance.from_dict(data, exclude_fields)
    
    def update_fields(self, **kwargs):
        """Update multiple fields at once"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Update the updated_at timestamp
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def get_table_name(cls) -> str:
        """Get the table name for this model"""
        return cls.__tablename__
    
    @classmethod
    def get_column_names(cls) -> List[str]:
        """Get list of column names for this model"""
        return [column.name for column in cls.__table__.columns]
    
    @classmethod
    def get_required_fields(cls) -> List[str]:
        """Get list of required (non-nullable) fields"""
        return [
            column.name for column in cls.__table__.columns
            if not column.nullable and column.default is None
        ]
    
    def validate(self) -> Dict[str, List[str]]:
        """Validate model instance and return any errors"""
        errors = {}
        
        # Check required fields
        for field_name in self.get_required_fields():
            value = getattr(self, field_name, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                if field_name not in errors:
                    errors[field_name] = []
                errors[field_name].append(f"{field_name} is required")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if model instance is valid"""
        return len(self.validate()) == 0
    
    def __repr__(self) -> str:
        """String representation of model instance"""
        class_name = self.__class__.__name__
        if hasattr(self, 'id') and self.id:
            return f"<{class_name}(id={self.id})>"
        else:
            return f"<{class_name}(new)>"
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        return self.__repr__()
    
    def __eq__(self, other) -> bool:
        """Check equality based on id"""
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id if self.id and other.id else False
    
    def __hash__(self) -> int:
        """Hash based on class and id"""
        return hash((self.__class__.__name__, self.id)) if self.id else hash(id(self))


class TimestampMixin:
    """Mixin for models that need timestamp tracking"""
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class SoftDeleteMixin:
    """Mixin for models that support soft deletion"""
    
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(String(1), default='N', nullable=False)  # 'Y' or 'N'
    
    def soft_delete(self):
        """Mark record as deleted without removing from database"""
        self.deleted_at = datetime.utcnow()
        self.is_deleted = 'Y'
    
    def restore(self):
        """Restore a soft-deleted record"""
        self.deleted_at = None
        self.is_deleted = 'N'
    
    @property
    def is_active(self) -> bool:
        """Check if record is not soft-deleted"""
        return self.is_deleted != 'Y'


# Global database manager instance
db_manager = DatabaseManager()


def get_db_session() -> Session:
    """Get database session - use this in repositories and services"""
    return db_manager.get_session()


def create_all_tables():
    """Create all database tables"""
    db_manager.create_tables()


def drop_all_tables():
    """Drop all database tables (use with caution!)"""
    db_manager.drop_tables()


# Example usage and testing
if __name__ == "__main__":
    
    # Example model to test base functionality
    class TestModel(BaseModel):
        name = Column(String(100), nullable=False)
        description = Column(String(500))
    
    # Create tables
    create_all_tables()
    
    # Test model creation
    session = get_db_session()
    try:
        test_item = TestModel(name="Test Item", description="This is a test")
        
        print("Model validation:", test_item.validate())
        print("Is valid:", test_item.is_valid())
        print("To dict:", test_item.to_dict())
        print("To JSON:", test_item.to_json())
        
        session.add(test_item)
        session.commit()
        
        print("Saved model:", test_item)
        
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()