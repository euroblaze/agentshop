#!/usr/bin/env python3
"""
Core Base Repository - Unified repository pattern implementation

Provides comprehensive CRUD operations and data access patterns
that are shared across all AgentShop modules.

Combines the best features from both webshop and backend repository implementations.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any, Callable, Union, Type
from sqlalchemy.orm import Session, Query
from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging
from contextlib import contextmanager

from ..orm import BaseModel
from ..orm.database import get_db_session

# Type variable for model classes
ModelType = TypeVar('ModelType', bound=BaseModel)

logger = logging.getLogger(__name__)


class RepositoryError(Exception):
    """Exception raised for repository operation errors"""
    
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.original_error = original_error


class BaseRepository(Generic[ModelType], ABC):
    """
    Abstract base repository providing comprehensive database operations.
    
    Features:
    - Full CRUD operations with error handling
    - Advanced querying with filters, pagination, and ordering
    - Bulk operations for performance
    - Search functionality
    - Transaction management
    - Context manager support
    - Flexible session handling
    """
    
    def __init__(self, model_class: Type[ModelType], session: Optional[Session] = None):
        """
        Initialize repository with model class and optional session.
        
        Args:
            model_class: The SQLAlchemy model class this repository manages
            session: Optional database session (will create if not provided)
        """
        self.model_class = model_class
        self._session = session
        self._auto_close_session = session is None
    
    @property 
    def session(self) -> Session:
        """Get database session, creating if needed."""
        if self._session is None:
            self._session = get_db_session()
            self._auto_close_session = True
        return self._session
    
    def set_session(self, session: Session, auto_close: bool = False):
        """
        Set the database session for this repository.
        
        Args:
            session: Database session to use
            auto_close: Whether to auto-close the session when done
        """
        if self._session and self._auto_close_session:
            self._session.close()
        
        self._session = session
        self._auto_close_session = auto_close
    
    @contextmanager
    def _session_scope(self):
        """Context manager for session handling with automatic cleanup."""
        session_created = False
        if self._session is None:
            self._session = get_db_session()
            session_created = True
        
        try:
            yield self._session
        except Exception:
            if session_created:
                self._session.rollback()
            raise
        finally:
            if session_created and self._auto_close_session:
                self._session.close()
                self._session = None
    
    # CRUD Operations
    
    def create(self, entity: ModelType, commit: bool = True) -> ModelType:
        """
        Create a new entity in the database.
        
        Args:
            entity: Model instance to create
            commit: Whether to commit immediately (default: True)
            
        Returns:
            Created entity with assigned ID
            
        Raises:
            RepositoryError: If creation fails
        """
        try:
            with self._session_scope() as session:
                session.add(entity)
                if commit:
                    session.commit()
                else:
                    session.flush()  # Get the ID without committing
                session.refresh(entity)
                return entity
        except (SQLAlchemyError, IntegrityError) as e:
            logger.error(f"Error creating {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Failed to create {self.model_class.__name__}", e)
    
    def create_from_dict(self, data: Dict[str, Any], commit: bool = True) -> ModelType:
        """
        Create entity from dictionary data.
        
        Args:
            data: Dictionary containing field values
            commit: Whether to commit immediately
            
        Returns:
            Created entity
        """
        entity = self.model_class()
        entity.from_dict(data)
        return self.create(entity, commit)
    
    def get_by_id(self, entity_id: int) -> Optional[ModelType]:
        """
        Get entity by ID.
        
        Args:
            entity_id: Primary key value
            
        Returns:
            Entity instance or None if not found
        """
        try:
            with self._session_scope() as session:
                return session.query(self.model_class).filter(
                    self.model_class.id == entity_id
                ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model_class.__name__} by ID {entity_id}: {e}")
            return None
    
    def get_all(self, 
                limit: Optional[int] = None, 
                offset: int = 0,
                order_by: Optional[str] = None,
                order_desc: bool = False,
                filters: Optional[Dict[str, Any]] = None) -> List[ModelType]:
        """
        Get all entities with optional pagination, ordering, and filtering.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            order_by: Field name to order by
            order_desc: Whether to order in descending order
            filters: Dictionary of field filters
            
        Returns:
            List of entity instances
        """
        try:
            with self._session_scope() as session:
                query = session.query(self.model_class)
                
                # Apply filters
                if filters:
                    for field_name, value in filters.items():
                        if hasattr(self.model_class, field_name):
                            field = getattr(self.model_class, field_name)
                            query = query.filter(field == value)
                
                # Apply ordering
                if order_by and hasattr(self.model_class, order_by):
                    order_field = getattr(self.model_class, order_by)
                    if order_desc:
                        query = query.order_by(desc(order_field))
                    else:
                        query = query.order_by(asc(order_field))
                
                # Apply pagination
                if offset > 0:
                    query = query.offset(offset)
                if limit:
                    query = query.limit(limit)
                
                return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting all {self.model_class.__name__}: {e}")
            return []
    
    def update(self, entity: ModelType, commit: bool = True) -> ModelType:
        """
        Update an existing entity.
        
        Args:
            entity: Model instance to update
            commit: Whether to commit immediately
            
        Returns:
            Updated entity
            
        Raises:
            RepositoryError: If update fails
        """
        try:
            with self._session_scope() as session:
                # Ensure entity is attached to session
                merged_entity = session.merge(entity)
                if commit:
                    session.commit()
                else:
                    session.flush()
                session.refresh(merged_entity)
                return merged_entity
        except (SQLAlchemyError, IntegrityError) as e:
            logger.error(f"Error updating {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Failed to update {self.model_class.__name__}", e)
    
    def update_by_id(self, entity_id: int, data: Dict[str, Any], commit: bool = True) -> Optional[ModelType]:
        """
        Update entity by ID with dictionary data.
        
        Args:
            entity_id: Primary key value
            data: Dictionary of field updates
            commit: Whether to commit immediately
            
        Returns:
            Updated entity or None if not found
        """
        entity = self.get_by_id(entity_id)
        if entity:
            entity.from_dict(data)
            return self.update(entity, commit)
        return None
    
    def delete(self, entity: ModelType, commit: bool = True) -> bool:
        """
        Delete an entity from the database.
        
        Args:
            entity: Model instance to delete
            commit: Whether to commit immediately
            
        Returns:
            True if deletion was successful
            
        Raises:
            RepositoryError: If deletion fails
        """
        try:
            with self._session_scope() as session:
                # Ensure entity is attached to session
                attached_entity = session.merge(entity)
                session.delete(attached_entity)
                if commit:
                    session.commit()
                else:
                    session.flush()
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Failed to delete {self.model_class.__name__}", e)
    
    def delete_by_id(self, entity_id: int, commit: bool = True) -> bool:
        """
        Delete entity by ID.
        
        Args:
            entity_id: Primary key value
            commit: Whether to commit immediately
            
        Returns:
            True if deletion was successful
        """
        entity = self.get_by_id(entity_id)
        if entity:
            return self.delete(entity, commit)
        return False
    
    def soft_delete_by_id(self, entity_id: int, commit: bool = True) -> bool:
        """
        Soft delete entity by ID (if entity supports soft deletion).
        
        Args:
            entity_id: Primary key value
            commit: Whether to commit immediately
            
        Returns:
            True if soft deletion was successful
        """
        entity = self.get_by_id(entity_id)
        if entity and hasattr(entity, 'soft_delete'):
            entity.soft_delete()
            self.update(entity, commit)
            return True
        return False
    
    # Query Operations
    
    def find_by(self, **criteria) -> List[ModelType]:
        """
        Find entities by criteria.
        
        Args:
            **criteria: Field name and value pairs
            
        Returns:
            List of matching entities
        """
        try:
            with self._session_scope() as session:
                query = session.query(self.model_class)
                
                for field_name, value in criteria.items():
                    if hasattr(self.model_class, field_name):
                        field = getattr(self.model_class, field_name)
                        if isinstance(value, (list, tuple)):
                            query = query.filter(field.in_(value))
                        else:
                            query = query.filter(field == value)
                
                return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error finding {self.model_class.__name__} by criteria {criteria}: {e}")
            return []
    
    def find_one_by(self, **criteria) -> Optional[ModelType]:
        """
        Find single entity by criteria.
        
        Args:
            **criteria: Field name and value pairs
            
        Returns:
            First matching entity or None
        """
        results = self.find_by(**criteria)
        return results[0] if results else None
    
    def count(self, **criteria) -> int:
        """
        Count entities matching criteria.
        
        Args:
            **criteria: Field name and value pairs
            
        Returns:
            Number of matching entities
        """
        try:
            with self._session_scope() as session:
                query = session.query(func.count(self.model_class.id))
                
                for field_name, value in criteria.items():
                    if hasattr(self.model_class, field_name):
                        field = getattr(self.model_class, field_name)
                        if isinstance(value, (list, tuple)):
                            query = query.filter(field.in_(value))
                        else:
                            query = query.filter(field == value)
                
                return query.scalar() or 0
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model_class.__name__}: {e}")
            return 0
    
    def exists(self, **criteria) -> bool:
        """
        Check if entity exists with given criteria.
        
        Args:
            **criteria: Field name and value pairs
            
        Returns:
            True if entity exists
        """
        return self.count(**criteria) > 0
    
    def exists_by_id(self, entity_id: int) -> bool:
        """Check if entity exists by ID."""
        return self.exists(id=entity_id)
    
    # Advanced Query Operations
    
    def find_by_complex(self, 
                       filters: Optional[List[Any]] = None,
                       order_by: Optional[str] = None,
                       order_desc: bool = False,
                       limit: Optional[int] = None,
                       offset: int = 0) -> List[ModelType]:
        """
        Find entities with complex filtering.
        
        Args:
            filters: List of SQLAlchemy filter expressions
            order_by: Field name to order by
            order_desc: Whether to order in descending order
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of matching entities
        """
        try:
            with self._session_scope() as session:
                query = session.query(self.model_class)
                
                # Apply filters
                if filters:
                    for filter_expr in filters:
                        query = query.filter(filter_expr)
                
                # Apply ordering
                if order_by and hasattr(self.model_class, order_by):
                    order_field = getattr(self.model_class, order_by)
                    if order_desc:
                        query = query.order_by(desc(order_field))
                    else:
                        query = query.order_by(asc(order_field))
                
                # Apply pagination
                if offset > 0:
                    query = query.offset(offset)
                if limit:
                    query = query.limit(limit)
                
                return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error in complex query for {self.model_class.__name__}: {e}")
            return []
    
    def search(self, 
               search_term: str,
               search_fields: List[str],
               limit: int = 50,
               offset: int = 0,
               case_sensitive: bool = False) -> List[ModelType]:
        """
        Search entities by text in specified fields.
        
        Args:
            search_term: Text to search for
            search_fields: List of field names to search in
            limit: Maximum number of results
            offset: Number of results to skip
            case_sensitive: Whether search should be case sensitive
            
        Returns:
            List of matching entities
        """
        try:
            if not search_term or not search_fields:
                return []
            
            with self._session_scope() as session:
                query = session.query(self.model_class)
                
                # Build OR conditions for all search fields
                search_conditions = []
                for field_name in search_fields:
                    if hasattr(self.model_class, field_name):
                        field = getattr(self.model_class, field_name)
                        if case_sensitive:
                            search_conditions.append(field.like(f"%{search_term}%"))
                        else:
                            search_conditions.append(field.ilike(f"%{search_term}%"))
                
                if search_conditions:
                    query = query.filter(or_(*search_conditions))
                
                if offset > 0:
                    query = query.offset(offset)
                
                return query.limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error searching {self.model_class.__name__}: {e}")
            return []
    
    # Bulk Operations
    
    def bulk_create(self, entities: List[ModelType], commit: bool = True) -> List[ModelType]:
        """
        Create multiple entities in a single transaction.
        
        Args:
            entities: List of model instances to create
            commit: Whether to commit immediately
            
        Returns:
            List of created entities
            
        Raises:
            RepositoryError: If bulk creation fails
        """
        try:
            with self._session_scope() as session:
                session.add_all(entities)
                if commit:
                    session.commit()
                else:
                    session.flush()
                
                # Refresh all entities to get their IDs
                for entity in entities:
                    session.refresh(entity)
                
                return entities
        except (SQLAlchemyError, IntegrityError) as e:
            logger.error(f"Error bulk creating {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Failed to bulk create {self.model_class.__name__}", e)
    
    def bulk_create_from_dicts(self, data_list: List[Dict[str, Any]], commit: bool = True) -> List[ModelType]:
        """
        Create multiple entities from dictionary data.
        
        Args:
            data_list: List of dictionaries containing field values
            commit: Whether to commit immediately
            
        Returns:
            List of created entities
        """
        entities = []
        for data in data_list:
            entity = self.model_class()
            entity.from_dict(data)
            entities.append(entity)
        
        return self.bulk_create(entities, commit)
    
    def bulk_update(self, updates: List[Dict[str, Any]], commit: bool = True) -> int:
        """
        Update multiple entities with different values.
        
        Args:
            updates: List of dicts with 'id' and field updates
            commit: Whether to commit immediately
            
        Returns:
            Number of entities updated
        """
        try:
            updated_count = 0
            with self._session_scope() as session:
                for update_data in updates:
                    entity_id = update_data.get('id')
                    if entity_id:
                        entity = session.query(self.model_class).filter(
                            self.model_class.id == entity_id
                        ).first()
                        
                        if entity:
                            entity.from_dict(update_data, exclude_fields=['id'])
                            updated_count += 1
                
                if commit:
                    session.commit()
                else:
                    session.flush()
                
                return updated_count
        except SQLAlchemyError as e:
            logger.error(f"Error bulk updating {self.model_class.__name__}: {e}")
            return 0
    
    def bulk_delete(self, entity_ids: List[int], commit: bool = True) -> int:
        """
        Delete multiple entities by their IDs.
        
        Args:
            entity_ids: List of entity IDs to delete
            commit: Whether to commit immediately
            
        Returns:
            Number of entities deleted
        """
        try:
            with self._session_scope() as session:
                deleted_count = session.query(self.model_class).filter(
                    self.model_class.id.in_(entity_ids)
                ).delete(synchronize_session=False)
                
                if commit:
                    session.commit()
                else:
                    session.flush()
                
                return deleted_count
        except SQLAlchemyError as e:
            logger.error(f"Error bulk deleting {self.model_class.__name__}: {e}")
            return 0
    
    # Utility Methods
    
    def get_model_class(self) -> Type[ModelType]:
        """Get the model class for this repository."""
        return self.model_class
    
    def get_table_name(self) -> str:
        """Get the table name for this repository's model."""
        return self.model_class.get_table_name()
    
    def validate_entity(self, entity: ModelType) -> Dict[str, List[str]]:
        """
        Validate an entity using its validation methods.
        
        Args:
            entity: Model instance to validate
            
        Returns:
            Dictionary of validation errors
        """
        return entity.validate() if hasattr(entity, 'validate') else {}
    
    def is_valid_entity(self, entity: ModelType) -> bool:
        """Check if an entity is valid."""
        return len(self.validate_entity(entity)) == 0
    
    # Transaction Management
    
    def begin_transaction(self):
        """Begin a new transaction."""
        self.session.begin()
    
    def commit(self):
        """Commit current transaction."""
        try:
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error committing transaction: {e}")
            raise RepositoryError("Failed to commit transaction", e)
    
    def rollback(self):
        """Rollback current transaction."""
        self.session.rollback()
    
    def flush(self):
        """Flush pending changes to database."""
        self.session.flush()
    
    def refresh(self, entity: ModelType):
        """Refresh entity from database."""
        self.session.refresh(entity)
    
    def close(self):
        """Close database session."""
        if self._session and self._auto_close_session:
            self._session.close()
            self._session = None
    
    # Context Manager Support
    
    def __enter__(self):
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if exc_type:
            self.rollback()
        else:
            try:
                self.commit()
            except Exception:
                self.rollback()
                raise
        finally:
            self.close()
    
    def __del__(self):
        """Cleanup when repository is destroyed."""
        self.close()