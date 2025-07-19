from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..orm.base_model import BaseModel, db_manager

T = TypeVar('T', bound=BaseModel)


class BaseRepository(Generic[T], ABC):
    """Abstract base repository with common CRUD operations"""
    
    def __init__(self, model_class: type[T]):
        self.model_class = model_class
        self.db_manager = db_manager
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.db_manager.get_session()
    
    def create(self, **kwargs) -> T:
        """Create a new entity"""
        session = self.get_session()
        try:
            entity = self.model_class(**kwargs)
            session.add(entity)
            session.commit()
            session.refresh(entity)
            return entity
        except IntegrityError as e:
            session.rollback()
            raise ValueError(f"Failed to create {self.model_class.__name__}: {str(e)}")
        finally:
            session.close()
    
    def get_by_id(self, entity_id: int) -> Optional[T]:
        """Get entity by ID"""
        session = self.get_session()
        try:
            return session.query(self.model_class).filter(self.model_class.id == entity_id).first()
        finally:
            session.close()
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """Get all entities with optional pagination"""
        session = self.get_session()
        try:
            query = session.query(self.model_class).offset(offset)
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()
    
    def update(self, entity_id: int, **kwargs) -> Optional[T]:
        """Update entity by ID"""
        session = self.get_session()
        try:
            entity = session.query(self.model_class).filter(self.model_class.id == entity_id).first()
            if entity:
                entity.update(**kwargs)
                session.commit()
                session.refresh(entity)
                return entity
            return None
        except IntegrityError as e:
            session.rollback()
            raise ValueError(f"Failed to update {self.model_class.__name__}: {str(e)}")
        finally:
            session.close()
    
    def delete(self, entity_id: int) -> bool:
        """Delete entity by ID"""
        session = self.get_session()
        try:
            entity = session.query(self.model_class).filter(self.model_class.id == entity_id).first()
            if entity:
                session.delete(entity)
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def find_by(self, **kwargs) -> List[T]:
        """Find entities by criteria"""
        session = self.get_session()
        try:
            query = session.query(self.model_class)
            for key, value in kwargs.items():
                if hasattr(self.model_class, key):
                    query = query.filter(getattr(self.model_class, key) == value)
            return query.all()
        finally:
            session.close()
    
    def find_one_by(self, **kwargs) -> Optional[T]:
        """Find single entity by criteria"""
        session = self.get_session()
        try:
            query = session.query(self.model_class)
            for key, value in kwargs.items():
                if hasattr(self.model_class, key):
                    query = query.filter(getattr(self.model_class, key) == value)
            return query.first()
        finally:
            session.close()
    
    def count(self, **kwargs) -> int:
        """Count entities with optional criteria"""
        session = self.get_session()
        try:
            query = session.query(self.model_class)
            for key, value in kwargs.items():
                if hasattr(self.model_class, key):
                    query = query.filter(getattr(self.model_class, key) == value)
            return query.count()
        finally:
            session.close()
    
    def exists(self, **kwargs) -> bool:
        """Check if entity exists with given criteria"""
        return self.count(**kwargs) > 0


class UnitOfWork:
    """Unit of Work pattern for managing transactions across multiple repositories"""
    
    def __init__(self):
        self.session = db_manager.get_session()
        self._committed = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        elif not self._committed:
            self.rollback()
        self.session.close()
    
    def commit(self):
        """Commit the transaction"""
        try:
            self.session.commit()
            self._committed = True
        except Exception:
            self.session.rollback()
            raise
    
    def rollback(self):
        """Rollback the transaction"""
        self.session.rollback()
    
    def add(self, entity):
        """Add entity to session"""
        self.session.add(entity)
    
    def delete(self, entity):
        """Delete entity from session"""
        self.session.delete(entity)
    
    def refresh(self, entity):
        """Refresh entity from database"""
        self.session.refresh(entity)