#!/usr/bin/env python3
"""
Core Base ORM Model - Unified implementation for all AgentShop modules

This module provides the foundational database model classes and mixins
that are shared across all AgentShop components including shop frontend,
admin backend, and customer-account systems.

Combines the best features from both the webshop and backend implementations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
import json
import re
from sqlalchemy import Column, Integer, DateTime, String, Boolean
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.sql import func

# Create base class for all models
Base = declarative_base()


class BaseModel(Base, ABC):
    """
    Abstract base model class with comprehensive functionality.
    
    Provides common fields, methods, and patterns for all database entities
    across the AgentShop ecosystem.
    
    Features:
    - Automatic table name generation from class name
    - Timestamp tracking (created_at, updated_at)
    - Serialization (to_dict, from_dict, to_json, from_json)
    - Validation framework
    - Field management utilities
    - Equality and hashing support
    """
    
    __abstract__ = True
    
    # Common fields for all models
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    @declared_attr
    def __tablename__(cls):
        """
        Generate table name from class name.
        Converts CamelCase to snake_case automatically.
        
        Example: ProductCategory -> product_category
        """
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
    
    def to_dict(self, exclude_fields: Optional[List[str]] = None, 
                include_relationships: bool = False) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.
        
        Args:
            exclude_fields: List of field names to exclude from output
            include_relationships: Whether to include relationship data
            
        Returns:
            Dictionary representation of the model
        """
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
        
        # Include relationships if requested
        if include_relationships:
            for relationship in self.__mapper__.relationships:
                rel_name = relationship.key
                if rel_name not in exclude_fields:
                    rel_value = getattr(self, rel_name, None)
                    if rel_value is not None:
                        if hasattr(rel_value, '__iter__') and not isinstance(rel_value, (str, bytes)):
                            # Collection relationship
                            result[rel_name] = [item.to_dict() if hasattr(item, 'to_dict') else str(item) 
                                              for item in rel_value]
                        else:
                            # Single relationship
                            result[rel_name] = rel_value.to_dict() if hasattr(rel_value, 'to_dict') else str(rel_value)
        
        return result
    
    def from_dict(self, data: Dict[str, Any], 
                  exclude_fields: Optional[List[str]] = None) -> 'BaseModel':
        """
        Update model instance from dictionary.
        
        Args:
            data: Dictionary containing field values
            exclude_fields: List of field names to exclude from update
            
        Returns:
            Updated model instance
        """
        exclude_fields = exclude_fields or ['id', 'created_at', 'updated_at']
        
        for key, value in data.items():
            if key not in exclude_fields and hasattr(self, key):
                # Handle datetime deserialization
                if isinstance(value, str) and hasattr(self.__table__.columns.get(key), 'type'):
                    column_type = self.__table__.columns.get(key).type
                    if isinstance(column_type, DateTime):
                        try:
                            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except (ValueError, AttributeError):
                            pass  # Keep original value if parsing fails
                
                setattr(self, key, value)
        
        return self
    
    def to_json(self, exclude_fields: Optional[List[str]] = None, 
                include_relationships: bool = False, indent: int = 2) -> str:
        """
        Convert model instance to JSON string.
        
        Args:
            exclude_fields: List of field names to exclude
            include_relationships: Whether to include relationship data
            indent: JSON indentation level
            
        Returns:
            JSON string representation
        """
        return json.dumps(
            self.to_dict(exclude_fields, include_relationships), 
            indent=indent, 
            ensure_ascii=False
        )
    
    @classmethod
    def from_json(cls, json_str: str, 
                  exclude_fields: Optional[List[str]] = None) -> 'BaseModel':
        """
        Create model instance from JSON string.
        
        Args:
            json_str: JSON string containing model data
            exclude_fields: List of field names to exclude
            
        Returns:
            New model instance
        """
        data = json.loads(json_str)
        instance = cls()
        return instance.from_dict(data, exclude_fields)
    
    def update_fields(self, **kwargs):
        """
        Update multiple fields at once and set updated_at timestamp.
        
        Args:
            **kwargs: Field names and values to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Update the updated_at timestamp
        self.updated_at = datetime.utcnow()
    
    def update(self, **kwargs):
        """Alias for update_fields for backward compatibility."""
        return self.update_fields(**kwargs)
    
    @classmethod
    def get_table_name(cls) -> str:
        """Get the table name for this model."""
        return cls.__tablename__
    
    @classmethod
    def get_column_names(cls) -> List[str]:
        """Get list of column names for this model."""
        return [column.name for column in cls.__table__.columns]
    
    @classmethod
    def get_required_fields(cls) -> List[str]:
        """Get list of required (non-nullable) fields excluding auto-generated ones."""
        return [
            column.name for column in cls.__table__.columns
            if not column.nullable 
            and column.default is None 
            and column.server_default is None
            and not column.autoincrement
        ]
    
    @classmethod
    def get_relationship_names(cls) -> List[str]:
        """Get list of relationship names for this model."""
        return [relationship.key for relationship in cls.__mapper__.relationships]
    
    def validate(self) -> Dict[str, List[str]]:
        """
        Validate model instance and return any errors.
        
        Returns:
            Dictionary with field names as keys and lists of error messages as values
        """
        errors = {}
        
        # Check required fields
        for field_name in self.get_required_fields():
            value = getattr(self, field_name, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                if field_name not in errors:
                    errors[field_name] = []
                errors[field_name].append(f"{field_name} is required")
        
        # Custom validation hook for subclasses
        custom_errors = self._custom_validation()
        for field_name, field_errors in custom_errors.items():
            if field_name not in errors:
                errors[field_name] = []
            errors[field_name].extend(field_errors)
        
        return errors
    
    def _custom_validation(self) -> Dict[str, List[str]]:
        """
        Override this method in subclasses to add custom validation logic.
        
        Returns:
            Dictionary with field names as keys and lists of error messages as values
        """
        return {}
    
    def is_valid(self) -> bool:
        """Check if model instance is valid."""
        return len(self.validate()) == 0
    
    def get_errors(self) -> Dict[str, List[str]]:
        """Get validation errors for this instance."""
        return self.validate()
    
    def __repr__(self) -> str:
        """String representation of model instance."""
        class_name = self.__class__.__name__
        if hasattr(self, 'id') and self.id:
            return f"<{class_name}(id={self.id})>"
        else:
            return f"<{class_name}(new)>"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return self.__repr__()
    
    def __eq__(self, other) -> bool:
        """Check equality based on class and id."""
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id if self.id and other.id else False
    
    def __hash__(self) -> int:
        """Hash based on class and id."""
        return hash((self.__class__.__name__, self.id)) if self.id else hash(id(self))


class TimestampMixin:
    """
    Mixin for models that need timestamp tracking.
    
    Provides created_at and updated_at fields with automatic management.
    """
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class SoftDeleteMixin:
    """
    Mixin for models that support soft deletion.
    
    Provides deleted_at and is_deleted fields with helper methods
    for marking records as deleted without removing them from the database.
    """
    
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    def soft_delete(self):
        """Mark record as deleted without removing from database."""
        self.deleted_at = datetime.utcnow()
        self.is_deleted = True
        self.updated_at = datetime.utcnow()
    
    def restore(self):
        """Restore a soft-deleted record."""
        self.deleted_at = None
        self.is_deleted = False
        self.updated_at = datetime.utcnow()
    
    @property
    def is_active(self) -> bool:
        """Check if record is not soft-deleted."""
        return not self.is_deleted
    
    def __repr__(self) -> str:
        """String representation including deletion status."""
        base_repr = super().__repr__()
        if self.is_deleted:
            return f"{base_repr[:-1]} deleted)>"
        return base_repr


class AuditMixin:
    """
    Mixin for models that need audit tracking.
    
    Provides fields to track who created and last modified a record.
    """
    
    created_by = Column(Integer, nullable=True)  # Foreign key to user
    updated_by = Column(Integer, nullable=True)  # Foreign key to user
    
    def set_created_by(self, user_id: int):
        """Set the creator of this record."""
        self.created_by = user_id
    
    def set_updated_by(self, user_id: int):
        """Set the last modifier of this record."""
        self.updated_by = user_id
        self.updated_at = datetime.utcnow()


class VersionMixin:
    """
    Mixin for models that need version tracking.
    
    Provides optimistic locking support through version numbers.
    """
    
    version = Column(Integer, default=1, nullable=False)
    
    def increment_version(self):
        """Increment the version number."""
        self.version += 1
        self.updated_at = datetime.utcnow()


# Export commonly used combinations
class FullAuditModel(BaseModel, SoftDeleteMixin, AuditMixin, VersionMixin):
    """
    Base model with full audit capabilities.
    
    Combines BaseModel with soft deletion, audit tracking, and versioning.
    Useful for critical business entities that need comprehensive tracking.
    """
    __abstract__ = True


class SimpleModel(BaseModel):
    """
    Simple model with just basic functionality.
    
    Inherits only from BaseModel without additional mixins.
    Useful for simple entities that don't need advanced features.
    """
    __abstract__ = True