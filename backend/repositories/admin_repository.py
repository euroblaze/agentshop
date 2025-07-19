#!/usr/bin/env python3
"""
Admin Repository - Data access layer for admin-related operations
Provides specialized queries and operations for admin users, sessions, and configuration
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta

from core.repositories.base_repository import BaseRepository
from ..models.admin_models import AdminUser, AdminSession, ConfigSetting, EmailTemplate


class AdminUserRepository(BaseRepository[AdminUser]):
    """Repository for AdminUser entities with specialized admin operations"""
    
    def __init__(self, session: Session = None):
        super().__init__(AdminUser, session)
    
    def get_by_username(self, username: str) -> Optional[AdminUser]:
        """
        Get admin user by username
        
        Args:
            username: Admin username
            
        Returns:
            AdminUser instance or None
        """
        return self.session.query(AdminUser).filter(
            AdminUser.username == username.lower()
        ).first()
    
    def get_by_email(self, email: str) -> Optional[AdminUser]:
        """
        Get admin user by email
        
        Args:
            email: Admin email address
            
        Returns:
            AdminUser instance or None
        """
        return self.session.query(AdminUser).filter(
            AdminUser.email == email.lower()
        ).first()
    
    def username_exists(self, username: str, exclude_user_id: int = None) -> bool:
        """
        Check if username already exists
        
        Args:
            username: Username to check
            exclude_user_id: Optional user ID to exclude from check
            
        Returns:
            True if username exists
        """
        query = self.session.query(AdminUser).filter(
            AdminUser.username == username.lower()
        )
        
        if exclude_user_id:
            query = query.filter(AdminUser.id != exclude_user_id)
        
        return query.first() is not None
    
    def email_exists(self, email: str, exclude_user_id: int = None) -> bool:
        """
        Check if email already exists
        
        Args:
            email: Email to check
            exclude_user_id: Optional user ID to exclude from check
            
        Returns:
            True if email exists
        """
        query = self.session.query(AdminUser).filter(
            AdminUser.email == email.lower()
        )
        
        if exclude_user_id:
            query = query.filter(AdminUser.id != exclude_user_id)
        
        return query.first() is not None
    
    def create_admin_user(self, username: str, email: str, password: str,
                         first_name: str, last_name: str,
                         is_superuser: bool = False,
                         created_by: str = None) -> AdminUser:
        """
        Create a new admin user
        
        Args:
            username: Admin username
            email: Admin email address
            password: Plain text password (will be hashed)
            first_name: Admin first name
            last_name: Admin last name
            is_superuser: Whether user has superuser privileges
            created_by: Username of admin who created this account
            
        Returns:
            Created admin user instance
            
        Raises:
            ValueError: If username or email already exists
        """
        if self.username_exists(username):
            raise ValueError("Username already exists")
        
        if self.email_exists(email):
            raise ValueError("Email already exists")
        
        admin_user = AdminUser(
            username=username.lower(),
            email=email.lower(),
            first_name=first_name,
            last_name=last_name,
            is_superuser=is_superuser,
            created_by=created_by
        )
        admin_user.set_password(password)
        
        return self.create(admin_user)
    
    def authenticate_admin(self, username: str, password: str) -> Optional[AdminUser]:
        """
        Authenticate admin user credentials
        
        Args:
            username: Admin username
            password: Plain text password
            
        Returns:
            AdminUser instance if authentication successful, None otherwise
        """
        admin_user = self.get_by_username(username)
        if admin_user and admin_user.is_active and admin_user.check_password(password):
            admin_user.record_login()
            return admin_user
        return None
    
    def get_active_admins(self) -> List[AdminUser]:
        """
        Get all active admin users
        
        Returns:
            List of active admin users
        """
        return self.session.query(AdminUser).filter(
            AdminUser.is_active == True
        ).order_by(AdminUser.username).all()
    
    def get_superusers(self) -> List[AdminUser]:
        """
        Get all superuser admin accounts
        
        Returns:
            List of superuser admin users
        """
        return self.session.query(AdminUser).filter(
            and_(
                AdminUser.is_superuser == True,
                AdminUser.is_active == True
            )
        ).order_by(AdminUser.username).all()
    
    def deactivate_admin(self, admin_id: int, reason: str = None) -> bool:
        """
        Deactivate admin user account
        
        Args:
            admin_id: Admin user ID
            reason: Optional reason for deactivation
            
        Returns:
            True if successful
        """
        try:
            admin_user = self.get_by_id(admin_id)
            if admin_user:
                admin_user.is_active = False
                if reason:
                    admin_user.notes = f"Deactivated: {reason}"
                return True
        except Exception:
            return False
        
        return False


class AdminSessionRepository(BaseRepository[AdminSession]):
    """Repository for AdminSession entities"""
    
    def __init__(self, session: Session = None):
        super().__init__(AdminSession, session)
    
    def create_session(self, admin_user_id: int, duration_hours: int = 8,
                      ip_address: str = None, user_agent: str = None) -> AdminSession:
        """
        Create a new admin session
        
        Args:
            admin_user_id: Admin user ID
            duration_hours: Session duration in hours
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Created session instance
        """
        session = AdminSession(
            admin_user_id=admin_user_id,
            duration_hours=duration_hours,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return self.create(session)
    
    def get_by_token(self, session_token: str) -> Optional[AdminSession]:
        """
        Get session by token
        
        Args:
            session_token: Session token
            
        Returns:
            AdminSession instance or None
        """
        return self.session.query(AdminSession).filter(
            AdminSession.session_token == session_token
        ).first()
    
    def get_valid_session(self, session_token: str) -> Optional[AdminSession]:
        """
        Get valid (non-expired, active) session by token
        
        Args:
            session_token: Session token
            
        Returns:
            Valid AdminSession instance or None
        """
        session = self.get_by_token(session_token)
        if session and session.is_valid():
            return session
        return None
    
    def get_admin_sessions(self, admin_user_id: int,
                          active_only: bool = True) -> List[AdminSession]:
        """
        Get all sessions for an admin user
        
        Args:
            admin_user_id: Admin user ID
            active_only: Whether to return only active sessions
            
        Returns:
            List of admin sessions
        """
        query = self.session.query(AdminSession).filter(
            AdminSession.admin_user_id == admin_user_id
        )
        
        if active_only:
            current_time = datetime.utcnow()
            query = query.filter(
                and_(
                    AdminSession.is_active == True,
                    AdminSession.expires_at > current_time
                )
            )
        
        return query.order_by(desc(AdminSession.created_at)).all()
    
    def invalidate_session(self, session_token: str) -> bool:
        """
        Invalidate a session
        
        Args:
            session_token: Session token to invalidate
            
        Returns:
            True if successful
        """
        try:
            self.session.query(AdminSession).filter(
                AdminSession.session_token == session_token
            ).update({
                AdminSession.is_active: False
            })
            return True
        except Exception:
            return False
    
    def invalidate_admin_sessions(self, admin_user_id: int) -> int:
        """
        Invalidate all sessions for an admin user
        
        Args:
            admin_user_id: Admin user ID
            
        Returns:
            Number of sessions invalidated
        """
        try:
            return self.session.query(AdminSession).filter(
                and_(
                    AdminSession.admin_user_id == admin_user_id,
                    AdminSession.is_active == True
                )
            ).update({
                AdminSession.is_active: False
            })
        except Exception:
            return 0
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions from database
        
        Returns:
            Number of sessions cleaned up
        """
        current_time = datetime.utcnow()
        expired_sessions = self.session.query(AdminSession).filter(
            AdminSession.expires_at < current_time
        ).all()
        
        count = len(expired_sessions)
        for expired_session in expired_sessions:
            self.session.delete(expired_session)
        
        return count
    
    def refresh_session(self, session_token: str, duration_hours: int = 8) -> bool:
        """
        Refresh session expiration
        
        Args:
            session_token: Session token to refresh
            duration_hours: New duration in hours
            
        Returns:
            True if successful
        """
        try:
            new_expiry = datetime.utcnow() + timedelta(hours=duration_hours)
            self.session.query(AdminSession).filter(
                AdminSession.session_token == session_token
            ).update({
                AdminSession.expires_at: new_expiry
            })
            return True
        except Exception:
            return False


class ConfigSettingRepository(BaseRepository[ConfigSetting]):
    """Repository for ConfigSetting entities"""
    
    def __init__(self, session: Session = None):
        super().__init__(ConfigSetting, session)
    
    def get_by_key(self, key: str) -> Optional[ConfigSetting]:
        """
        Get configuration setting by key
        
        Args:
            key: Configuration key
            
        Returns:
            ConfigSetting instance or None
        """
        return self.session.query(ConfigSetting).filter(
            ConfigSetting.key == key
        ).first()
    
    def get_setting_value(self, key: str, default=None):
        """
        Get typed configuration value by key
        
        Args:
            key: Configuration key
            default: Default value if setting not found
            
        Returns:
            Typed configuration value
        """
        setting = self.get_by_key(key)
        if setting:
            return setting.get_typed_value()
        return default
    
    def set_setting_value(self, key: str, value: Any, description: str = None,
                         data_type: str = None, category: str = None,
                         is_sensitive: bool = False) -> ConfigSetting:
        """
        Set configuration value by key
        
        Args:
            key: Configuration key
            value: Configuration value
            description: Setting description
            data_type: Data type (string, integer, float, boolean, json)
            category: Setting category
            is_sensitive: Whether setting contains sensitive data
            
        Returns:
            ConfigSetting instance
        """
        setting = self.get_by_key(key)
        if setting:
            setting.set_typed_value(value)
            if description:
                setting.description = description
        else:
            setting = ConfigSetting(
                key=key,
                description=description or f"Configuration setting: {key}",
                data_type=data_type or 'string',
                category=category or 'general',
                is_sensitive=is_sensitive
            )
            setting.set_typed_value(value)
            setting = self.create(setting)
        
        return setting
    
    def get_settings_by_category(self, category: str) -> List[ConfigSetting]:
        """
        Get all settings in a category
        
        Args:
            category: Settings category
            
        Returns:
            List of configuration settings
        """
        return self.session.query(ConfigSetting).filter(
            ConfigSetting.category == category
        ).order_by(ConfigSetting.key).all()
    
    def get_all_categories(self) -> List[str]:
        """
        Get all available setting categories
        
        Returns:
            List of category names
        """
        result = self.session.query(ConfigSetting.category).distinct().all()
        return [row[0] for row in result if row[0]]
    
    def get_sensitive_settings(self) -> List[ConfigSetting]:
        """
        Get all sensitive configuration settings
        
        Returns:
            List of sensitive settings
        """
        return self.session.query(ConfigSetting).filter(
            ConfigSetting.is_sensitive == True
        ).order_by(ConfigSetting.category, ConfigSetting.key).all()
    
    def export_settings(self, exclude_sensitive: bool = True) -> Dict[str, Any]:
        """
        Export all settings as dictionary
        
        Args:
            exclude_sensitive: Whether to exclude sensitive settings
            
        Returns:
            Dictionary of settings
        """
        query = self.session.query(ConfigSetting)
        
        if exclude_sensitive:
            query = query.filter(ConfigSetting.is_sensitive == False)
        
        settings = query.all()
        
        result = {}
        for setting in settings:
            result[setting.key] = {
                'value': setting.get_typed_value(),
                'description': setting.description,
                'category': setting.category,
                'data_type': setting.data_type
            }
        
        return result
    
    def import_settings(self, settings_data: Dict[str, Any]) -> int:
        """
        Import settings from dictionary
        
        Args:
            settings_data: Dictionary of settings to import
            
        Returns:
            Number of settings imported
        """
        imported_count = 0
        
        for key, data in settings_data.items():
            try:
                if isinstance(data, dict):
                    self.set_setting_value(
                        key=key,
                        value=data.get('value'),
                        description=data.get('description'),
                        data_type=data.get('data_type', 'string'),
                        category=data.get('category', 'general')
                    )
                else:
                    self.set_setting_value(key, data)
                
                imported_count += 1
            except Exception:
                continue
        
        return imported_count


class EmailTemplateRepository(BaseRepository[EmailTemplate]):
    """Repository for EmailTemplate entities"""
    
    def __init__(self, session: Session = None):
        super().__init__(EmailTemplate, session)
    
    def get_by_name(self, name: str) -> Optional[EmailTemplate]:
        """
        Get email template by name
        
        Args:
            name: Template name
            
        Returns:
            EmailTemplate instance or None
        """
        return self.session.query(EmailTemplate).filter(
            and_(
                EmailTemplate.name == name,
                EmailTemplate.is_active == True
            )
        ).first()
    
    def get_templates_by_category(self, category: str) -> List[EmailTemplate]:
        """
        Get email templates by category
        
        Args:
            category: Template category
            
        Returns:
            List of email templates
        """
        return self.session.query(EmailTemplate).filter(
            and_(
                EmailTemplate.category == category,
                EmailTemplate.is_active == True
            )
        ).order_by(EmailTemplate.name).all()
    
    def get_active_templates(self) -> List[EmailTemplate]:
        """
        Get all active email templates
        
        Returns:
            List of active email templates
        """
        return self.session.query(EmailTemplate).filter(
            EmailTemplate.is_active == True
        ).order_by(EmailTemplate.category, EmailTemplate.name).all()
    
    def create_template(self, name: str, subject: str, html_content: str,
                       text_content: str = None, description: str = None,
                       category: str = 'general',
                       variables: List[str] = None) -> EmailTemplate:
        """
        Create a new email template
        
        Args:
            name: Template name (unique)
            subject: Email subject template
            html_content: HTML email content
            text_content: Plain text email content
            description: Template description
            category: Template category
            variables: List of available template variables
            
        Returns:
            Created email template instance
            
        Raises:
            ValueError: If template name already exists
        """
        existing = self.get_by_name(name)
        if existing:
            raise ValueError("Template name already exists")
        
        template = EmailTemplate(
            name=name,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            description=description,
            category=category
        )
        
        if variables:
            template.set_variables(variables)
        
        return self.create(template)
    
    def render_template(self, template_name: str, 
                       variables: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Render email template with variables
        
        Args:
            template_name: Name of template to render
            variables: Variables to substitute in template
            
        Returns:
            Dictionary with rendered subject, html_content, text_content
        """
        template = self.get_by_name(template_name)
        if template:
            return template.render(variables)
        return None
    
    def get_template_categories(self) -> List[str]:
        """
        Get all template categories
        
        Returns:
            List of category names
        """
        result = self.session.query(EmailTemplate.category).distinct().all()
        return [row[0] for row in result if row[0]]


def create_default_admin_user(session: Session, username: str = "admin", 
                             password: str = "admin123") -> AdminUser:
    """
    Create default admin user if none exists
    
    Args:
        session: Database session
        username: Admin username
        password: Admin password
        
    Returns:
        Created or existing admin user
    """
    admin_repo = AdminUserRepository(session)
    
    # Check if any admin users exist
    existing_admin = admin_repo.get_all(limit=1)
    if existing_admin:
        return existing_admin[0]
    
    # Create default admin user
    admin_user = admin_repo.create_admin_user(
        username=username,
        email="admin@agentshop.com",
        password=password,
        first_name="Admin",
        last_name="User",
        is_superuser=True,
        created_by="system"
    )
    
    return admin_user