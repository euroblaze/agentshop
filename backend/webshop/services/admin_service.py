#!/usr/bin/env python3
"""
Admin Service - Business logic for admin user management and system configuration
Handles admin authentication, configuration management, and email templates
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
import logging

from .base_service import BaseService, ValidationError, ServiceError
from ..repositories.admin_repository import (
    AdminUserRepository, AdminSessionRepository, 
    ConfigSettingRepository, EmailTemplateRepository
)
from ..models.admin_models import AdminUser, AdminSession, ConfigSetting, EmailTemplate

logger = logging.getLogger(__name__)


class AdminUserService(BaseService[AdminUser]):
    """Service for AdminUser entity with authentication and user management"""
    
    def __init__(self, repository: AdminUserRepository = None, session: Session = None):
        super().__init__(repository, session)
        self.session_service = AdminSessionService(session=session)
    
    def _create_repository(self) -> AdminUserRepository:
        """Create AdminUserRepository instance"""
        return AdminUserRepository(self._session)
    
    def _create_entity_from_data(self, entity_data: Dict[str, Any]) -> AdminUser:
        """Create AdminUser instance from data dictionary"""
        return AdminUser(**entity_data)
    
    def _validate_business_rules(self, admin_user: AdminUser,
                                is_create: bool = True) -> Dict[str, List[str]]:
        """Validate admin user business rules"""
        errors = {}
        
        # Username uniqueness check
        if is_create or admin_user.username:
            if self.repository.username_exists(admin_user.username, 
                                             admin_user.id if not is_create else None):
                errors['username'] = ['Username already exists']
        
        # Email uniqueness check
        if is_create or admin_user.email:
            if self.repository.email_exists(admin_user.email,
                                          admin_user.id if not is_create else None):
                errors['email'] = ['Email address already exists']
        
        # Password strength validation (for new users)
        if is_create and hasattr(admin_user, '_plain_password'):
            password_errors = self._validate_password_strength(admin_user._plain_password)
            if password_errors:
                errors['password'] = password_errors
        
        return errors
    
    def _apply_create_business_rules(self, admin_user: AdminUser, entity_data: Dict[str, Any]):
        """Apply business rules during admin user creation"""
        # Set default values
        admin_user.is_active = True
        admin_user.login_count = 0
        
        # Store creator information
        admin_user.created_by = entity_data.get('created_by', 'system')
    
    def _after_create(self, admin_user: AdminUser, entity_data: Dict[str, Any]):
        """Log admin user creation"""
        try:
            logger.info(f"Admin user created: {admin_user.username}")
        except Exception as e:
            logger.error(f"Error logging admin user creation: {e}")
    
    def _get_default_search_fields(self) -> List[str]:
        """Get default search fields for admin users"""
        return ['username', 'first_name', 'last_name', 'email']
    
    # Admin Authentication and Management
    
    def create_admin_user(self, username: str, email: str, password: str,
                         first_name: str, last_name: str,
                         is_superuser: bool = False,
                         created_by: str = None) -> AdminUser:
        """
        Create new admin user
        
        Args:
            username: Admin username
            email: Admin email address
            password: Plain text password
            first_name: Admin first name
            last_name: Admin last name
            is_superuser: Whether user has superuser privileges
            created_by: Username of admin who created this account
            
        Returns:
            Created admin user instance
            
        Raises:
            ValidationError: If admin data is invalid
            ServiceError: If creation fails
        """
        try:
            admin_data = {
                'username': username.lower().strip(),
                'email': email.lower().strip(),
                'first_name': first_name.strip(),
                'last_name': last_name.strip(),
                'is_superuser': is_superuser,
                'created_by': created_by,
                '_plain_password': password
            }
            
            # Create admin user
            admin_user = self.create(admin_data)
            
            # Set password (will be hashed)
            admin_user.set_password(password)
            self.repository.update(admin_user)
            
            return admin_user
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating admin user: {e}")
            raise ServiceError("Failed to create admin user") from e
    
    def authenticate_admin(self, username: str, password: str,
                          ip_address: str = None, user_agent: str = None) -> Optional[Tuple[AdminUser, AdminSession]]:
        """
        Authenticate admin user and create session
        
        Args:
            username: Admin username
            password: Plain text password
            ip_address: Login IP address
            user_agent: Login user agent
            
        Returns:
            Tuple of (AdminUser, AdminSession) if successful, None otherwise
        """
        try:
            # Authenticate admin
            admin_user = self.repository.authenticate_admin(username, password)
            if not admin_user:
                return None
            
            # Create session (shorter duration than customer sessions)
            session = self.session_service.create_session(
                admin_user.id, duration_hours=8,
                ip_address=ip_address, user_agent=user_agent
            )
            
            return admin_user, session
            
        except Exception as e:
            logger.error(f"Error authenticating admin: {e}")
            return None
    
    def logout_admin(self, session_token: str) -> bool:
        """Logout admin by invalidating session"""
        try:
            return self.session_service.invalidate_session(session_token)
        except Exception as e:
            logger.error(f"Error logging out admin: {e}")
            return False
    
    def get_admin_by_session(self, session_token: str) -> Optional[AdminUser]:
        """Get admin user by valid session token"""
        try:
            session = self.session_service.get_valid_session(session_token)
            if session:
                return self.get_by_id(session.admin_user_id)
            return None
        except Exception as e:
            logger.error(f"Error getting admin by session: {e}")
            return None
    
    def reset_admin_password(self, admin_id: int, new_password: str) -> bool:
        """Reset admin password (for superuser use)"""
        try:
            # Validate password strength
            password_errors = self._validate_password_strength(new_password)
            if password_errors:
                raise ValidationError("Invalid password", {'password': password_errors})
            
            admin_user = self.get_by_id(admin_id)
            if admin_user:
                admin_user.set_password(new_password)
                self.repository.update(admin_user)
                
                # Invalidate all sessions for security
                self.session_service.invalidate_admin_sessions(admin_id)
                
                logger.info(f"Password reset for admin: {admin_user.username}")
                return True
            return False
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error resetting admin password: {e}")
            return False
    
    def change_admin_password(self, admin_id: int, current_password: str,
                             new_password: str) -> bool:
        """Change admin password with current password verification"""
        try:
            admin_user = self.get_by_id(admin_id)
            if not admin_user or not admin_user.check_password(current_password):
                raise ValidationError("Current password is incorrect")
            
            # Validate new password strength
            password_errors = self._validate_password_strength(new_password)
            if password_errors:
                raise ValidationError("Invalid new password", {'password': password_errors})
            
            admin_user.set_password(new_password)
            self.repository.update(admin_user)
            
            # Invalidate other sessions for security
            active_sessions = self.session_service.get_admin_sessions(admin_id, active_only=True)
            for session in active_sessions[1:]:  # Keep current session
                self.session_service.invalidate_session(session.session_token)
            
            logger.info(f"Password changed for admin: {admin_user.username}")
            return True
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error changing admin password: {e}")
            return False
    
    def deactivate_admin(self, admin_id: int, reason: str = None) -> bool:
        """Deactivate admin account"""
        try:
            admin_user = self.get_by_id(admin_id)
            if admin_user:
                admin_user.is_active = False
                if reason:
                    admin_user.notes = f"Deactivated: {reason}"
                self.repository.update(admin_user)
                
                # Invalidate all sessions
                self.session_service.invalidate_admin_sessions(admin_id)
                
                logger.info(f"Admin account deactivated: {admin_user.username}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deactivating admin: {e}")
            return False
    
    def get_active_admins(self) -> List[AdminUser]:
        """Get all active admin users"""
        try:
            return self.repository.get_active_admins()
        except Exception as e:
            logger.error(f"Error getting active admins: {e}")
            return []
    
    def get_superusers(self) -> List[AdminUser]:
        """Get all superuser admin accounts"""
        try:
            return self.repository.get_superusers()
        except Exception as e:
            logger.error(f"Error getting superusers: {e}")
            return []
    
    def _validate_password_strength(self, password: str) -> List[str]:
        """Validate admin password strength (stricter than customer passwords)"""
        errors = []
        
        if len(password) < 12:
            errors.append("Password must be at least 12 characters long")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        # Check for common weak passwords
        weak_passwords = ['password', 'admin', 'administrator', '123456789012']
        if password.lower() in weak_passwords:
            errors.append("Password is too common")
        
        return errors


class AdminSessionService(BaseService[AdminSession]):
    """Service for AdminSession entity"""
    
    def __init__(self, repository: AdminSessionRepository = None, session: Session = None):
        super().__init__(repository, session)
    
    def _create_repository(self) -> AdminSessionRepository:
        """Create AdminSessionRepository instance"""
        return AdminSessionRepository(self._session)
    
    def _create_entity_from_data(self, entity_data: Dict[str, Any]) -> AdminSession:
        """Create AdminSession instance from data dictionary"""
        return AdminSession(**entity_data)
    
    def create_session(self, admin_user_id: int, duration_hours: int = 8,
                      ip_address: str = None, user_agent: str = None) -> AdminSession:
        """Create new admin session"""
        try:
            return self.repository.create_session(
                admin_user_id, duration_hours, ip_address, user_agent
            )
        except Exception as e:
            logger.error(f"Error creating admin session: {e}")
            raise ServiceError("Failed to create session") from e
    
    def get_valid_session(self, session_token: str) -> Optional[AdminSession]:
        """Get valid session by token"""
        try:
            return self.repository.get_valid_session(session_token)
        except Exception as e:
            logger.error(f"Error getting valid session: {e}")
            return None
    
    def invalidate_session(self, session_token: str) -> bool:
        """Invalidate session"""
        try:
            return self.repository.invalidate_session(session_token)
        except Exception as e:
            logger.error(f"Error invalidating session: {e}")
            return False
    
    def invalidate_admin_sessions(self, admin_user_id: int) -> int:
        """Invalidate all sessions for an admin user"""
        try:
            return self.repository.invalidate_admin_sessions(admin_user_id)
        except Exception as e:
            logger.error(f"Error invalidating admin sessions: {e}")
            return 0
    
    def get_admin_sessions(self, admin_user_id: int, active_only: bool = True) -> List[AdminSession]:
        """Get sessions for an admin user"""
        try:
            return self.repository.get_admin_sessions(admin_user_id, active_only)
        except Exception as e:
            logger.error(f"Error getting admin sessions: {e}")
            return []
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        try:
            return self.repository.cleanup_expired_sessions()
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0


class ConfigurationService(BaseService[ConfigSetting]):
    """Service for system configuration management"""
    
    def __init__(self, repository: ConfigSettingRepository = None, session: Session = None):
        super().__init__(repository, session)
    
    def _create_repository(self) -> ConfigSettingRepository:
        """Create ConfigSettingRepository instance"""
        return ConfigSettingRepository(self._session)
    
    def _create_entity_from_data(self, entity_data: Dict[str, Any]) -> ConfigSetting:
        """Create ConfigSetting instance from data dictionary"""
        return ConfigSetting(**entity_data)
    
    def get_setting(self, key: str, default=None):
        """Get configuration setting value"""
        try:
            return self.repository.get_setting_value(key, default)
        except Exception as e:
            logger.error(f"Error getting setting {key}: {e}")
            return default
    
    def set_setting(self, key: str, value: Any, description: str = None,
                   data_type: str = None, category: str = None,
                   is_sensitive: bool = False) -> bool:
        """Set configuration setting value"""
        try:
            self.repository.set_setting_value(
                key, value, description, data_type, category, is_sensitive
            )
            return True
        except Exception as e:
            logger.error(f"Error setting {key}: {e}")
            return False
    
    def get_settings_by_category(self, category: str) -> List[ConfigSetting]:
        """Get all settings in a category"""
        try:
            return self.repository.get_settings_by_category(category)
        except Exception as e:
            logger.error(f"Error getting settings for category {category}: {e}")
            return []
    
    def get_all_categories(self) -> List[str]:
        """Get all available setting categories"""
        try:
            return self.repository.get_all_categories()
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    def export_settings(self, exclude_sensitive: bool = True) -> Dict[str, Any]:
        """Export all settings as dictionary"""
        try:
            return self.repository.export_settings(exclude_sensitive)
        except Exception as e:
            logger.error(f"Error exporting settings: {e}")
            return {}
    
    def import_settings(self, settings_data: Dict[str, Any]) -> int:
        """Import settings from dictionary"""
        try:
            return self.repository.import_settings(settings_data)
        except Exception as e:
            logger.error(f"Error importing settings: {e}")
            return 0
    
    def get_email_settings(self) -> Dict[str, Any]:
        """Get email configuration settings"""
        email_settings = {}
        email_keys = [
            'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password',
            'site_email', 'admin_email'
        ]
        
        for key in email_keys:
            email_settings[key] = self.get_setting(key)
        
        return email_settings
    
    def get_payment_settings(self) -> Dict[str, Any]:
        """Get payment configuration settings"""
        payment_settings = {}
        payment_keys = [
            'stripe_public_key', 'stripe_secret_key',
            'paypal_client_id', 'paypal_client_secret',
            'tax_rate'
        ]
        
        for key in payment_keys:
            payment_settings[key] = self.get_setting(key)
        
        return payment_settings
    
    def initialize_default_settings(self) -> int:
        """Initialize default configuration settings"""
        try:
            from ..models.admin_models import create_default_settings
            create_default_settings(self.session)
            return len(self.repository.get_all())
        except Exception as e:
            logger.error(f"Error initializing default settings: {e}")
            return 0


class EmailTemplateService(BaseService[EmailTemplate]):
    """Service for email template management"""
    
    def __init__(self, repository: EmailTemplateRepository = None, session: Session = None):
        super().__init__(repository, session)
    
    def _create_repository(self) -> EmailTemplateRepository:
        """Create EmailTemplateRepository instance"""
        return EmailTemplateRepository(self._session)
    
    def _create_entity_from_data(self, entity_data: Dict[str, Any]) -> EmailTemplate:
        """Create EmailTemplate instance from data dictionary"""
        return EmailTemplate(**entity_data)
    
    def _validate_business_rules(self, template: EmailTemplate,
                                is_create: bool = True) -> Dict[str, List[str]]:
        """Validate email template business rules"""
        errors = {}
        
        # Template name uniqueness check
        if is_create or template.name:
            existing = self.repository.get_by_name(template.name)
            if existing and existing.id != template.id:
                errors['name'] = ['Template name already exists']
        
        return errors
    
    def get_template_by_name(self, name: str) -> Optional[EmailTemplate]:
        """Get email template by name"""
        try:
            return self.repository.get_by_name(name)
        except Exception as e:
            logger.error(f"Error getting template {name}: {e}")
            return None
    
    def render_template(self, template_name: str, variables: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Render email template with variables"""
        try:
            return self.repository.render_template(template_name, variables)
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            return None
    
    def get_templates_by_category(self, category: str) -> List[EmailTemplate]:
        """Get email templates by category"""
        try:
            return self.repository.get_templates_by_category(category)
        except Exception as e:
            logger.error(f"Error getting templates for category {category}: {e}")
            return []
    
    def get_active_templates(self) -> List[EmailTemplate]:
        """Get all active email templates"""
        try:
            return self.repository.get_active_templates()
        except Exception as e:
            logger.error(f"Error getting active templates: {e}")
            return []
    
    def create_template(self, name: str, subject: str, html_content: str,
                       text_content: str = None, description: str = None,
                       category: str = 'general',
                       variables: List[str] = None) -> EmailTemplate:
        """Create new email template"""
        try:
            return self.repository.create_template(
                name, subject, html_content, text_content,
                description, category, variables
            )
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            raise ServiceError("Failed to create email template") from e
    
    def get_template_categories(self) -> List[str]:
        """Get all template categories"""
        try:
            return self.repository.get_template_categories()
        except Exception as e:
            logger.error(f"Error getting template categories: {e}")
            return []
    
    def initialize_default_templates(self) -> int:
        """Initialize default email templates"""
        default_templates = [
            {
                'name': 'customer_welcome',
                'subject': 'Welcome to AgentShop!',
                'html_content': '''
                <h2>Welcome to AgentShop, {first_name}!</h2>
                <p>Thank you for creating an account with us.</p>
                <p>Please click the link below to verify your email address:</p>
                <p><a href="{verification_link}">Verify Email</a></p>
                ''',
                'text_content': '''
                Welcome to AgentShop, {first_name}!
                
                Thank you for creating an account with us.
                
                Please visit the following link to verify your email address:
                {verification_link}
                ''',
                'category': 'customer',
                'variables': ['first_name', 'verification_link']
            },
            {
                'name': 'order_confirmation',
                'subject': 'Order Confirmation #{order_number}',
                'html_content': '''
                <h2>Order Confirmation</h2>
                <p>Thank you for your order, {customer_name}!</p>
                <p><strong>Order Number:</strong> {order_number}</p>
                <p><strong>Total:</strong> ${total_amount}</p>
                <p>Your download links:</p>
                <ul>{download_links}</ul>
                ''',
                'text_content': '''
                Order Confirmation
                
                Thank you for your order, {customer_name}!
                
                Order Number: {order_number}
                Total: ${total_amount}
                
                Your download links:
                {download_links}
                ''',
                'category': 'order',
                'variables': ['customer_name', 'order_number', 'total_amount', 'download_links']
            }
        ]
        
        created_count = 0
        for template_data in default_templates:
            try:
                existing = self.get_template_by_name(template_data['name'])
                if not existing:
                    self.create_template(**template_data)
                    created_count += 1
            except Exception as e:
                logger.error(f"Error creating default template: {e}")
        
        return created_count