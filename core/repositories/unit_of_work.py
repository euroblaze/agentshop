#!/usr/bin/env python3
"""
Unit of Work Pattern Implementation

Provides transaction management across multiple repositories
for maintaining data consistency in complex operations.
"""

from typing import Dict, Type, Optional, Any, TypeVar, Generic
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from ..orm.database import get_db_session
from .base_repository import BaseRepository, RepositoryError

logger = logging.getLogger(__name__)

RepositoryType = TypeVar('RepositoryType', bound=BaseRepository)


class UnitOfWork:
    """
    Unit of Work pattern implementation for managing transactions across multiple repositories.
    
    Provides a single transaction context that can span multiple repository operations,
    ensuring data consistency and proper transaction management.
    
    Features:
    - Shared session across all repositories
    - Automatic transaction management
    - Repository factory and caching
    - Context manager support
    - Comprehensive error handling and rollback
    """
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize unit of work with optional session.
        
        Args:
            session: Database session to use (will create if not provided)
        """
        self._session = session or get_db_session()
        self._repositories: Dict[Type, BaseRepository] = {}
        self._committed = False
        self._rolled_back = False
        self._session_created = session is None
    
    @property
    def session(self) -> Session:
        """Get the shared database session."""
        return self._session
    
    def get_repository(self, 
                      repository_class: Type[RepositoryType], 
                      model_class: Optional[Type] = None) -> RepositoryType:
        """
        Get repository instance for the given class with shared session.
        
        Args:
            repository_class: Repository class to instantiate
            model_class: Model class if not inferrable from repository
            
        Returns:
            Repository instance with shared session
        """
        if repository_class not in self._repositories:
            try:
                if model_class:
                    repo = repository_class(model_class, self._session)
                else:
                    # Try to instantiate with just session
                    repo = repository_class(session=self._session)
                
                # Ensure repository doesn't auto-close our shared session
                if hasattr(repo, 'set_session'):
                    repo.set_session(self._session, auto_close=False)
                
                self._repositories[repository_class] = repo
            except Exception as e:
                logger.error(f"Failed to create repository {repository_class.__name__}: {e}")
                raise RepositoryError(f"Failed to create repository {repository_class.__name__}", e)
        
        return self._repositories[repository_class]
    
    def register_repository(self, repository: BaseRepository, repository_type: Optional[Type] = None):
        """
        Register an existing repository instance with this unit of work.
        
        Args:
            repository: Repository instance to register
            repository_type: Type key for the repository (defaults to repository's class)
        """
        repo_type = repository_type or type(repository)
        
        # Set the repository to use our shared session
        if hasattr(repository, 'set_session'):
            repository.set_session(self._session, auto_close=False)
        
        self._repositories[repo_type] = repository
    
    def add(self, entity):
        """
        Add entity to the session.
        
        Args:
            entity: Model instance to add
        """
        self._session.add(entity)
    
    def add_all(self, entities):
        """
        Add multiple entities to the session.
        
        Args:
            entities: List of model instances to add
        """
        self._session.add_all(entities)
    
    def delete(self, entity):
        """
        Mark entity for deletion in the session.
        
        Args:
            entity: Model instance to delete
        """
        self._session.delete(entity)
    
    def merge(self, entity):
        """
        Merge entity into the session.
        
        Args:
            entity: Model instance to merge
            
        Returns:
            Merged entity instance
        """
        return self._session.merge(entity)
    
    def refresh(self, entity):
        """
        Refresh entity from database.
        
        Args:
            entity: Model instance to refresh
        """
        self._session.refresh(entity)
    
    def flush(self):
        """
        Flush pending changes to database without committing.
        
        Raises:
            RepositoryError: If flush fails
        """
        try:
            self._session.flush()
        except SQLAlchemyError as e:
            logger.error(f"Error flushing unit of work: {e}")
            raise RepositoryError("Failed to flush unit of work", e)
    
    def commit(self):
        """
        Commit all changes in the unit of work.
        
        Raises:
            RepositoryError: If commit fails
        """
        if self._committed:
            logger.warning("Unit of work already committed")
            return
        
        if self._rolled_back:
            raise RepositoryError("Cannot commit after rollback")
        
        try:
            self._session.commit()
            self._committed = True
            logger.debug("Unit of work committed successfully")
        except SQLAlchemyError as e:
            self._session.rollback()
            self._rolled_back = True
            logger.error(f"Error committing unit of work: {e}")
            raise RepositoryError("Failed to commit unit of work", e)
    
    def rollback(self):
        """Rollback all changes in the unit of work."""
        if not self._rolled_back:
            self._session.rollback()
            self._rolled_back = True
            logger.debug("Unit of work rolled back")
    
    def close(self):
        """Close the unit of work and clean up resources."""
        # Close all repositories
        for repo in self._repositories.values():
            if hasattr(repo, 'close'):
                try:
                    repo.close()
                except Exception as e:
                    logger.warning(f"Error closing repository: {e}")
        
        # Close session if we created it
        if self._session and self._session_created:
            try:
                self._session.close()
            except Exception as e:
                logger.warning(f"Error closing session: {e}")
        
        self._repositories.clear()
    
    def is_committed(self) -> bool:
        """Check if the unit of work has been committed."""
        return self._committed
    
    def is_rolled_back(self) -> bool:
        """Check if the unit of work has been rolled back."""
        return self._rolled_back
    
    def is_active(self) -> bool:
        """Check if the unit of work is still active (not committed or rolled back)."""
        return not (self._committed or self._rolled_back)
    
    def get_repository_count(self) -> int:
        """Get the number of registered repositories."""
        return len(self._repositories)
    
    def get_repository_types(self) -> list:
        """Get list of registered repository types."""
        return list(self._repositories.keys())
    
    def clear_repositories(self):
        """Clear all registered repositories."""
        for repo in self._repositories.values():
            if hasattr(repo, 'close'):
                repo.close()
        self._repositories.clear()
    
    # Context Manager Support
    
    def __enter__(self):
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager with automatic transaction management."""
        try:
            if exc_type is not None:
                # Exception occurred - rollback
                self.rollback()
                logger.debug(f"Unit of work rolled back due to exception: {exc_type.__name__}")
            elif not self._committed and not self._rolled_back:
                # No exception and not manually committed - auto commit
                self.commit()
                logger.debug("Unit of work auto-committed")
        except Exception as e:
            logger.error(f"Error in unit of work exit: {e}")
            # Ensure rollback if commit failed
            if not self._rolled_back:
                self.rollback()
            # Re-raise the exception
            raise
        finally:
            self.close()
    
    def __del__(self):
        """Cleanup when unit of work is destroyed."""
        if not (self._committed or self._rolled_back):
            logger.warning("Unit of work destroyed without commit or rollback")
            self.rollback()
        self.close()


class UnitOfWorkManager:
    """
    Manager for creating and managing multiple units of work.
    
    Useful for complex operations that need multiple transaction contexts
    or for managing nested transactions.
    """
    
    def __init__(self):
        self._active_uows: Dict[str, UnitOfWork] = {}
    
    def create_unit_of_work(self, name: str = "default", session: Optional[Session] = None) -> UnitOfWork:
        """
        Create a new unit of work with optional name.
        
        Args:
            name: Name identifier for the unit of work
            session: Optional session to use
            
        Returns:
            New UnitOfWork instance
        """
        if name in self._active_uows:
            raise ValueError(f"Unit of work '{name}' already exists")
        
        uow = UnitOfWork(session)
        self._active_uows[name] = uow
        return uow
    
    def get_unit_of_work(self, name: str = "default") -> Optional[UnitOfWork]:
        """
        Get an existing unit of work by name.
        
        Args:
            name: Name of the unit of work
            
        Returns:
            UnitOfWork instance or None if not found
        """
        return self._active_uows.get(name)
    
    def commit_all(self):
        """Commit all active units of work."""
        errors = []
        for name, uow in self._active_uows.items():
            try:
                if uow.is_active():
                    uow.commit()
            except Exception as e:
                errors.append(f"Failed to commit UoW '{name}': {e}")
        
        if errors:
            raise RepositoryError(f"Failed to commit some units of work: {'; '.join(errors)}")
    
    def rollback_all(self):
        """Rollback all active units of work."""
        for uow in self._active_uows.values():
            if uow.is_active():
                uow.rollback()
    
    def close_all(self):
        """Close all units of work."""
        for uow in self._active_uows.values():
            uow.close()
        self._active_uows.clear()
    
    def remove_unit_of_work(self, name: str):
        """
        Remove and close a unit of work.
        
        Args:
            name: Name of the unit of work to remove
        """
        if name in self._active_uows:
            uow = self._active_uows.pop(name)
            uow.close()
    
    def get_active_count(self) -> int:
        """Get the number of active units of work."""
        return len(self._active_uows)
    
    def get_active_names(self) -> list:
        """Get names of all active units of work."""
        return list(self._active_uows.keys())


# Global unit of work manager instance
uow_manager = UnitOfWorkManager()


def create_unit_of_work(name: str = "default", session: Optional[Session] = None) -> UnitOfWork:
    """
    Create a new unit of work using the global manager.
    
    Args:
        name: Name identifier for the unit of work
        session: Optional session to use
        
    Returns:
        New UnitOfWork instance
    """
    return uow_manager.create_unit_of_work(name, session)


def get_unit_of_work(name: str = "default") -> Optional[UnitOfWork]:
    """
    Get an existing unit of work by name.
    
    Args:
        name: Name of the unit of work
        
    Returns:
        UnitOfWork instance or None if not found
    """
    return uow_manager.get_unit_of_work(name)