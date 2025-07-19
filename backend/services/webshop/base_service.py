#!/usr/bin/env python3
"""
Base Service - Abstract service layer implementation
Provides common business logic patterns and repository coordination
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any, Callable
from sqlalchemy.orm import Session
import logging

from core.repositories.base_repository import BaseRepository, RepositoryError
from core.repositories.unit_of_work import UnitOfWork
from core.orm.base_model import BaseModel

# Type variable for model classes
ModelType = TypeVar('ModelType', bound=BaseModel)

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Exception raised for service layer errors"""
    pass


class ValidationError(ServiceError):
    """Exception raised for validation errors"""
    
    def __init__(self, message: str, errors: Dict[str, List[str]] = None):
        super().__init__(message)
        self.errors = errors or {}


class BaseService(Generic[ModelType], ABC):
    """Abstract base service providing common business logic patterns"""
    
    def __init__(self, repository: BaseRepository[ModelType] = None, 
                 session: Session = None):
        """
        Initialize service with repository and optional session
        
        Args:
            repository: Repository instance for data access
            session: Optional database session
        """
        self._repository = repository
        self._session = session
        self._unit_of_work = None
        
        # Initialize repository if not provided
        if self._repository is None:
            self._repository = self._create_repository()
        
        # Set session on repository if provided
        if self._session and self._repository:
            self._repository.set_session(self._session)
    
    @property
    def repository(self) -> BaseRepository[ModelType]:
        """Get repository instance"""
        if self._repository is None:
            self._repository = self._create_repository()
        return self._repository
    
    @property
    def session(self) -> Session:
        """Get database session"""
        if self._session is None:
            self._session = self.repository.session
        return self._session
    
    @abstractmethod
    def _create_repository(self) -> BaseRepository[ModelType]:
        """Create repository instance - must be implemented by subclasses"""
        pass
    
    def set_unit_of_work(self, unit_of_work: UnitOfWork):
        """Set unit of work for transaction management"""
        self._unit_of_work = unit_of_work
        if unit_of_work and self._repository:
            self._repository.set_session(unit_of_work._session)
    
    # CRUD Operations with Business Logic
    
    def create(self, entity_data: Dict[str, Any], 
               validate: bool = True) -> ModelType:
        """
        Create new entity with validation and business rules
        
        Args:
            entity_data: Dictionary with entity data
            validate: Whether to validate entity before creation
            
        Returns:
            Created entity instance
            
        Raises:
            ValidationError: If validation fails
            ServiceError: If creation fails
        """
        try:
            # Create entity instance
            entity = self._create_entity_from_data(entity_data)
            
            # Validate if required
            if validate:
                self._validate_entity(entity, is_create=True)
            
            # Apply business rules
            self._apply_create_business_rules(entity, entity_data)
            
            # Create in repository
            created_entity = self.repository.create(entity)
            
            # Post-creation actions
            self._after_create(created_entity, entity_data)
            
            return created_entity
            
        except ValidationError:
            raise
        except RepositoryError as e:
            logger.error(f"Repository error in {self.__class__.__name__}.create: {e}")
            raise ServiceError(f"Failed to create {self._get_entity_name()}") from e
        except Exception as e:
            logger.error(f"Unexpected error in {self.__class__.__name__}.create: {e}")
            raise ServiceError(f"Failed to create {self._get_entity_name()}") from e
    
    def get_by_id(self, entity_id: int) -> Optional[ModelType]:
        """
        Get entity by ID with business logic
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Entity instance or None
        """
        try:
            entity = self.repository.get_by_id(entity_id)
            if entity:
                # Apply business rules for retrieval
                self._apply_get_business_rules(entity)
            return entity
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}.get_by_id: {e}")
            return None
    
    def get_all(self, filters: Dict[str, Any] = None, 
                limit: int = None, offset: int = None,
                order_by: str = None, order_desc: bool = False) -> List[ModelType]:
        """
        Get all entities with filtering and pagination
        
        Args:
            filters: Optional filters to apply
            limit: Maximum number of results
            offset: Number of results to skip
            order_by: Field to order by
            order_desc: Whether to order in descending order
            
        Returns:
            List of entities
        """
        try:
            # Apply default filters
            if filters is None:
                filters = {}
            filters.update(self._get_default_filters())
            
            # Get entities from repository
            if filters:
                entities = self.repository.find_by(**filters)
            else:
                entities = self.repository.get_all(limit, offset, order_by, order_desc)
            
            # Apply business rules for each entity
            for entity in entities:
                self._apply_get_business_rules(entity)
            
            return entities
            
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}.get_all: {e}")
            return []
    
    def update(self, entity_id: int, update_data: Dict[str, Any],
               validate: bool = True) -> Optional[ModelType]:
        """
        Update entity with validation and business rules
        
        Args:
            entity_id: Entity ID to update
            update_data: Dictionary with updated data
            validate: Whether to validate entity after update
            
        Returns:
            Updated entity instance or None
            
        Raises:
            ValidationError: If validation fails
            ServiceError: If update fails
        """
        try:
            # Get existing entity
            entity = self.repository.get_by_id(entity_id)
            if not entity:
                return None
            
            # Store original state for business rules
            original_entity = self._clone_entity(entity)
            
            # Apply updates
            self._apply_updates_to_entity(entity, update_data)
            
            # Validate if required
            if validate:
                self._validate_entity(entity, is_create=False)
            
            # Apply business rules
            self._apply_update_business_rules(entity, update_data, original_entity)
            
            # Update in repository
            updated_entity = self.repository.update(entity)
            
            # Post-update actions
            self._after_update(updated_entity, update_data, original_entity)
            
            return updated_entity
            
        except ValidationError:
            raise
        except RepositoryError as e:
            logger.error(f"Repository error in {self.__class__.__name__}.update: {e}")
            raise ServiceError(f"Failed to update {self._get_entity_name()}") from e
        except Exception as e:
            logger.error(f"Unexpected error in {self.__class__.__name__}.update: {e}")
            raise ServiceError(f"Failed to update {self._get_entity_name()}") from e
    
    def delete(self, entity_id: int, soft_delete: bool = False) -> bool:
        """
        Delete entity with business rules
        
        Args:
            entity_id: Entity ID to delete
            soft_delete: Whether to perform soft delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            ServiceError: If deletion fails or is not allowed
        """
        try:
            # Get entity
            entity = self.repository.get_by_id(entity_id)
            if not entity:
                return False
            
            # Check if deletion is allowed
            if not self._can_delete(entity):
                raise ServiceError(f"Cannot delete {self._get_entity_name()}")
            
            # Apply business rules before deletion
            self._apply_delete_business_rules(entity)
            
            # Perform deletion
            if soft_delete and hasattr(entity, 'soft_delete'):
                entity.soft_delete()
                self.repository.update(entity)
            else:
                self.repository.delete(entity)
            
            # Post-deletion actions
            self._after_delete(entity)
            
            return True
            
        except ServiceError:
            raise
        except RepositoryError as e:
            logger.error(f"Repository error in {self.__class__.__name__}.delete: {e}")
            raise ServiceError(f"Failed to delete {self._get_entity_name()}") from e
        except Exception as e:
            logger.error(f"Unexpected error in {self.__class__.__name__}.delete: {e}")
            raise ServiceError(f"Failed to delete {self._get_entity_name()}") from e
    
    def search(self, search_term: str, search_fields: List[str] = None,
               filters: Dict[str, Any] = None, limit: int = 50) -> List[ModelType]:
        """
        Search entities with business logic
        
        Args:
            search_term: Text to search for
            search_fields: Fields to search in
            filters: Additional filters
            limit: Maximum number of results
            
        Returns:
            List of matching entities
        """
        try:
            # Get default search fields if not provided
            if search_fields is None:
                search_fields = self._get_default_search_fields()
            
            # Apply default filters
            if filters is None:
                filters = {}
            filters.update(self._get_default_filters())
            
            # Perform search
            entities = self.repository.search(search_term, search_fields, limit)
            
            # Apply additional filters
            if filters:
                filtered_entities = []
                for entity in entities:
                    if self._entity_matches_filters(entity, filters):
                        filtered_entities.append(entity)
                entities = filtered_entities
            
            # Apply business rules
            for entity in entities:
                self._apply_get_business_rules(entity)
            
            return entities
            
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}.search: {e}")
            return []
    
    # Abstract methods for subclasses to implement
    
    @abstractmethod
    def _create_entity_from_data(self, entity_data: Dict[str, Any]) -> ModelType:
        """Create entity instance from data dictionary"""
        pass
    
    def _validate_entity(self, entity: ModelType, is_create: bool = True):
        """
        Validate entity and raise ValidationError if invalid
        
        Args:
            entity: Entity to validate
            is_create: Whether this is a create operation
            
        Raises:
            ValidationError: If validation fails
        """
        # Use model validation
        errors = entity.validate()
        
        # Add business logic validation
        business_errors = self._validate_business_rules(entity, is_create)
        for field, field_errors in business_errors.items():
            if field in errors:
                errors[field].extend(field_errors)
            else:
                errors[field] = field_errors
        
        if errors:
            raise ValidationError("Validation failed", errors)
    
    def _validate_business_rules(self, entity: ModelType, 
                                is_create: bool = True) -> Dict[str, List[str]]:
        """
        Validate business rules - override in subclasses
        
        Args:
            entity: Entity to validate
            is_create: Whether this is a create operation
            
        Returns:
            Dictionary of validation errors
        """
        return {}
    
    def _apply_create_business_rules(self, entity: ModelType, 
                                   entity_data: Dict[str, Any]):
        """Apply business rules during creation - override in subclasses"""
        pass
    
    def _apply_update_business_rules(self, entity: ModelType,
                                   update_data: Dict[str, Any],
                                   original_entity: ModelType):
        """Apply business rules during update - override in subclasses"""
        pass
    
    def _apply_delete_business_rules(self, entity: ModelType):
        """Apply business rules during deletion - override in subclasses"""
        pass
    
    def _apply_get_business_rules(self, entity: ModelType):
        """Apply business rules during retrieval - override in subclasses"""
        pass
    
    def _after_create(self, entity: ModelType, entity_data: Dict[str, Any]):
        """Post-creation actions - override in subclasses"""
        pass
    
    def _after_update(self, entity: ModelType, update_data: Dict[str, Any],
                     original_entity: ModelType):
        """Post-update actions - override in subclasses"""
        pass
    
    def _after_delete(self, entity: ModelType):
        """Post-deletion actions - override in subclasses"""
        pass
    
    def _can_delete(self, entity: ModelType) -> bool:
        """Check if entity can be deleted - override in subclasses"""
        return True
    
    def _get_default_filters(self) -> Dict[str, Any]:
        """Get default filters for queries - override in subclasses"""
        return {}
    
    def _get_default_search_fields(self) -> List[str]:
        """Get default search fields - override in subclasses"""
        return []
    
    def _get_entity_name(self) -> str:
        """Get entity name for error messages"""
        if hasattr(self, 'repository') and hasattr(self.repository, 'model_class'):
            return self.repository.model_class.__name__
        return "Entity"
    
    # Helper methods
    
    def _apply_updates_to_entity(self, entity: ModelType, 
                                update_data: Dict[str, Any]):
        """Apply update data to entity"""
        for field, value in update_data.items():
            if hasattr(entity, field):
                setattr(entity, field, value)
    
    def _clone_entity(self, entity: ModelType) -> ModelType:
        """Create a copy of entity for comparison"""
        # Simple implementation - could be enhanced with deep copy
        entity_data = entity.to_dict()
        return self._create_entity_from_data(entity_data)
    
    def _entity_matches_filters(self, entity: ModelType, 
                               filters: Dict[str, Any]) -> bool:
        """Check if entity matches filter criteria"""
        for field, value in filters.items():
            if hasattr(entity, field):
                entity_value = getattr(entity, field)
                if entity_value != value:
                    return False
        return True
    
    # Transaction Management
    
    def commit(self):
        """Commit current transaction"""
        if self._unit_of_work:
            self._unit_of_work.commit()
        else:
            self.repository.commit()
    
    def rollback(self):
        """Rollback current transaction"""
        if self._unit_of_work:
            self._unit_of_work.rollback()
        else:
            self.repository.rollback()


class ServiceManager:
    """Manages service instances and provides dependency injection"""
    
    def __init__(self, session: Session = None):
        """
        Initialize service manager
        
        Args:
            session: Optional database session for all services
        """
        self._session = session
        self._services: Dict[type, BaseService] = {}
        self._unit_of_work: Optional[UnitOfWork] = None
    
    def get_service(self, service_class: type) -> BaseService:
        """
        Get service instance
        
        Args:
            service_class: Service class to instantiate
            
        Returns:
            Service instance
        """
        if service_class not in self._services:
            service = service_class(session=self._session)
            if self._unit_of_work:
                service.set_unit_of_work(self._unit_of_work)
            self._services[service_class] = service
        
        return self._services[service_class]
    
    def set_unit_of_work(self, unit_of_work: UnitOfWork):
        """Set unit of work for all services"""
        self._unit_of_work = unit_of_work
        for service in self._services.values():
            service.set_unit_of_work(unit_of_work)
    
    def commit_all(self):
        """Commit all services"""
        if self._unit_of_work:
            self._unit_of_work.commit()
        else:
            for service in self._services.values():
                service.commit()
    
    def rollback_all(self):
        """Rollback all services"""
        if self._unit_of_work:
            self._unit_of_work.rollback()
        else:
            for service in self._services.values():
                service.rollback()


# Context manager for transactional service operations
class ServiceTransaction:
    """Context manager for transactional service operations"""
    
    def __init__(self, *services: BaseService):
        """
        Initialize transaction context
        
        Args:
            *services: Service instances to include in transaction
        """
        self.services = services
        self.unit_of_work = UnitOfWork()
    
    def __enter__(self):
        """Enter transaction context"""
        for service in self.services:
            service.set_unit_of_work(self.unit_of_work)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit transaction context"""
        if exc_type:
            self.unit_of_work.rollback()
        else:
            try:
                self.unit_of_work.commit()
            except:
                self.unit_of_work.rollback()
                raise
        finally:
            self.unit_of_work.close()