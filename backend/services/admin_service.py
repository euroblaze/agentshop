#!/usr/bin/env python3
"""
Admin Service - Business logic for admin operations
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from ..models.admin_models import AdminUser
from ..core.orm.base_model import db_manager


class AdminUserService:
    """Service for admin user management operations"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or db_manager.get_session()
    
    def get_by_id(self, admin_id: int) -> Optional[AdminUser]:
        """Get admin user by ID"""
        return self.session.query(AdminUser).filter(AdminUser.id == admin_id).first()
    
    def get_by_username(self, username: str) -> Optional[AdminUser]:
        """Get admin user by username"""
        return self.session.query(AdminUser).filter(AdminUser.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[AdminUser]:
        """Get admin user by email"""
        return self.session.query(AdminUser).filter(AdminUser.email == email).first()
    
    def create_admin(self, admin_data: Dict[str, Any]) -> AdminUser:
        """Create a new admin user"""
        admin = AdminUser(**admin_data)
        self.session.add(admin)
        self.session.commit()
        return admin
    
    def update_admin(self, admin_id: int, update_data: Dict[str, Any]) -> Optional[AdminUser]:
        """Update admin information"""
        admin = self.get_by_id(admin_id)
        if admin:
            for key, value in update_data.items():
                if hasattr(admin, key):
                    setattr(admin, key, value)
            self.session.commit()
        return admin
    
    def authenticate_admin(self, username: str, password: str) -> Optional[AdminUser]:
        """Authenticate admin with username and password"""
        admin = self.get_by_username(username)
        if admin and admin.check_password(password) and admin.is_active:
            return admin
        return None