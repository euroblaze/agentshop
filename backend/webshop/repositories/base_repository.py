#!/usr/bin/env python3
"""
Base Repository - Abstract repository pattern implementation
Provides common CRUD operations and database access patterns
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any, Callable
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.exc import SQLAlchemyError
import logging

from ..orm.base_model import BaseModel, get_db_session

# Type variable for model classes
ModelType = TypeVar('ModelType', bound=BaseModel)

logger = logging.getLogger(__name__)


class BaseRepository(Generic[ModelType], ABC):
    """Abstract base repository providing common database operations"""
    
    def __init__(self, model_class: type, session: Session = None):
        """
        Initialize repository with model class and optional session
        
        Args:
            model_class: The SQLAlchemy model class this repository manages
            session: Optional database session (will create if not provided)
        """
        self.model_class = model_class
        self._session = session
        
    @property 
    def session(self) -> Session:
        """Get database session, creating if needed"""
        if self._session is None:
            self._session = get_db_session()
        return self._session
    
    def set_session(self, session: Session):
        """Set the database session for this repository"""
        self._session = session
    
    # CRUD Operations
    
    def create(self, entity: ModelType) -> ModelType:
        """
        Create a new entity in the database
        
        Args:
            entity: Model instance to create
            
        Returns:
            Created entity with assigned ID
            
        Raises:
            RepositoryError: If creation fails
        """
        try:
            self.session.add(entity)
            self.session.flush()  # Get the ID without committing
            return entity
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error creating {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Failed to create {self.model_class.__name__}") from e
    
    def get_by_id(self, entity_id: int) -> Optional[ModelType]:
        """
        Get entity by ID
        
        Args:
            entity_id: Primary key value
            
        Returns:
            Entity instance or None if not found
        """
        try:
            return self.session.query(self.model_class).filter(
                self.model_class.id == entity_id
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model_class.__name__} by ID {entity_id}: {e}")
            return None
    
    def get_all(self, 
                limit: int = None, 
                offset: int = None,
                order_by: str = None,
                order_desc: bool = False) -> List[ModelType]:
        """
        Get all entities with optional pagination and ordering
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            order_by: Field name to order by
            order_desc: Whether to order in descending order
            
        Returns:
            List of entity instances
        """
        try:
            query = self.session.query(self.model_class)
            
            # Apply ordering
            if order_by and hasattr(self.model_class, order_by):
                order_field = getattr(self.model_class, order_by)
                if order_desc:
                    query = query.order_by(desc(order_field))
                else:
                    query = query.order_by(asc(order_field))
            
            # Apply pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting all {self.model_class.__name__}: {e}")
            return []
    
    def update(self, entity: ModelType) -> ModelType:
        """
        Update an existing entity
        
        Args:
            entity: Model instance to update
            
        Returns:
            Updated entity
            
        Raises:
            RepositoryError: If update fails
        """
        try:
            # Ensure entity is attached to session
            merged_entity = self.session.merge(entity)
            self.session.flush()
            return merged_entity
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error updating {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Failed to update {self.model_class.__name__}") from e
    
    def delete(self, entity: ModelType) -> bool:
        """
        Delete an entity from the database
        
        Args:
            entity: Model instance to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            RepositoryError: If deletion fails
        """
        try:
            self.session.delete(entity)
            self.session.flush()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error deleting {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Failed to delete {self.model_class.__name__}") from e
    
    def delete_by_id(self, entity_id: int) -> bool:
        """
        Delete entity by ID
        
        Args:
            entity_id: Primary key value
            
        Returns:
            True if deletion was successful
        """
        entity = self.get_by_id(entity_id)
        if entity:
            return self.delete(entity)
        return False
    
    # Query Operations
    
    def find_by(self, **criteria) -> List[ModelType]:
        """
        Find entities by criteria
        
        Args:
            **criteria: Field name and value pairs
            
        Returns:
            List of matching entities
        """
        try:
            query = self.session.query(self.model_class)
            
            for field_name, value in criteria.items():
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    query = query.filter(field == value)
            
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error finding {self.model_class.__name__} by criteria {criteria}: {e}")
            return []
    
    def find_one_by(self, **criteria) -> Optional[ModelType]:
        """
        Find single entity by criteria
        
        Args:
            **criteria: Field name and value pairs
            
        Returns:
            First matching entity or None
        """
        results = self.find_by(**criteria)
        return results[0] if results else None
    
    def count(self, **criteria) -> int:
        """
        Count entities matching criteria
        
        Args:
            **criteria: Field name and value pairs
            
        Returns:
            Number of matching entities
        """
        try:
            query = self.session.query(self.model_class)
            
            for field_name, value in criteria.items():
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    query = query.filter(field == value)
            
            return query.count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model_class.__name__}: {e}")
            return 0
    
    def exists(self, **criteria) -> bool:
        """
        Check if entity exists with given criteria
        
        Args:
            **criteria: Field name and value pairs
            
        Returns:
            True if entity exists
        """
        return self.count(**criteria) > 0
    
    # Advanced Query Operations
    
    def find_by_complex(self, 
                       filters: List[Any] = None,
                       order_by: str = None,
                       order_desc: bool = False,
                       limit: int = None,
                       offset: int = None) -> List[ModelType]:
        """
        Find entities with complex filtering
        
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
            query = self.session.query(self.model_class)
            
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
            if offset:
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
               limit: int = 50) -> List[ModelType]:
        """
        Search entities by text in specified fields
        
        Args:
            search_term: Text to search for
            search_fields: List of field names to search in
            limit: Maximum number of results
            
        Returns:
            List of matching entities
        """
        try:
            if not search_term or not search_fields:
                return []
            
            query = self.session.query(self.model_class)
            
            # Build OR conditions for all search fields
            search_conditions = []
            for field_name in search_fields:
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    search_conditions.append(field.ilike(f"%{search_term}%"))
            
            if search_conditions:
                query = query.filter(or_(*search_conditions))
            
            return query.limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error searching {self.model_class.__name__}: {e}")
            return []
    
    # Bulk Operations
    
    def bulk_create(self, entities: List[ModelType]) -> List[ModelType]:
        """
        Create multiple entities in a single transaction
        
        Args:
            entities: List of model instances to create
            
        Returns:
            List of created entities
            
        Raises:
            RepositoryError: If bulk creation fails
        """
        try:
            self.session.add_all(entities)
            self.session.flush()
            return entities
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error bulk creating {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Failed to bulk create {self.model_class.__name__}") from e
    
    def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """
        Update multiple entities with different values
        
        Args:
            updates: List of dicts with 'id' and field updates
            
        Returns:
            Number of entities updated
        """
        try:
            updated_count = 0
            for update_data in updates:
                entity_id = update_data.get('id')
                if entity_id:
                    entity = self.get_by_id(entity_id)
                    if entity:
                        for field, value in update_data.items():
                            if field != 'id' and hasattr(entity, field):
                                setattr(entity, field, value)
                        updated_count += 1
            
            self.session.flush()
            return updated_count
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error bulk updating {self.model_class.__name__}: {e}")
            return 0
    
    # Transaction Management
    
    def commit(self):
        """Commit current transaction"""
        try:
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error committing transaction: {e}")
            raise RepositoryError("Failed to commit transaction") from e
    
    def rollback(self):
        """Rollback current transaction"""
        self.session.rollback()
    
    def close(self):
        """Close database session"""
        if self._session:
            self._session.close()
            self._session = None
    
    # Context Manager Support
    
    def __enter__(self):
        """Enter context manager"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager"""
        if exc_type:
            self.rollback()
        else:
            try:
                self.commit()
            except:
                self.rollback()
                raise
        finally:
            self.close()


class RepositoryError(Exception):
    """Exception raised for repository operation errors"""
    pass


class UnitOfWork:
    """
    Unit of Work pattern implementation for managing transactions across multiple repositories
    """
    
    def __init__(self, session: Session = None):
        """
        Initialize unit of work with optional session
        
        Args:
            session: Database session to use (will create if not provided)
        """
        self._session = session or get_db_session()
        self._repositories: Dict[type, BaseRepository] = {}
    
    def get_repository(self, repository_class: type, model_class: type = None) -> BaseRepository:
        """
        Get repository instance for the given class
        
        Args:
            repository_class: Repository class to instantiate
            model_class: Model class if not inferrable from repository
            
        Returns:
            Repository instance with shared session
        """
        if repository_class not in self._repositories:
            if model_class:
                repo = repository_class(model_class, self._session)
            else:
                repo = repository_class(self._session)
            self._repositories[repository_class] = repo
        
        return self._repositories[repository_class]
    
    def commit(self):
        """Commit all changes in the unit of work"""
        try:
            self._session.commit()
        except SQLAlchemyError as e:
            self._session.rollback()
            logger.error(f"Error committing unit of work: {e}")
            raise RepositoryError("Failed to commit unit of work") from e
    
    def rollback(self):
        """Rollback all changes in the unit of work"""
        self._session.rollback()
    
    def close(self):
        """Close the unit of work and session"""
        self._session.close()
    
    def __enter__(self):
        """Enter context manager"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager"""
        if exc_type:
            self.rollback()
        else:
            try:
                self.commit()
            except:
                self.rollback()
                raise
        finally:
            self.close()


# Example usage demonstration
if __name__ == "__main__":
    # This would normally be done with concrete repository classes
    from ..models.product_models import Product
    
    class TestProductRepository(BaseRepository[Product]):
        def __init__(self, session: Session = None):
            super().__init__(Product, session)
    
    # Example usage
    with UnitOfWork() as uow:
        product_repo = uow.get_repository(TestProductRepository, Product)
        
        # Create a test product
        product = Product(
            name="Test Product",
            title="Test Product Title",
            short_description="A test product",
            full_description="This is a detailed test product description"
        )
        
        created_product = product_repo.create(product)
        print(f"Created product: {created_product}")
        
        # Find products
        products = product_repo.find_by(name="Test Product")
        print(f"Found {len(products)} products")
        
        # Search products
        search_results = product_repo.search("test", ["name", "title"])
        print(f"Search found {len(search_results)} products")