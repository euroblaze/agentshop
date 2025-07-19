#!/usr/bin/env python3
"""
Admin Models - Database models for admin user management and configuration
Handles admin authentication, sessions, and system configuration
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.orm import relationship
from typing import Dict, Any, List, Optional
import hashlib
import secrets
from datetime import datetime, timedelta
import json

from core.orm.base_model import BaseModel


class AdminUser(BaseModel):
    """Admin user model for backend management"""
    
    __tablename__ = 'admin_users'
    
    # Authentication fields
    username = Column(String(100), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    
    # Account status and permissions
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    
    # Password reset functionality
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    
    # Admin metadata
    created_by = Column(String(100))  # Username of admin who created this account
    notes = Column(Text)              # Admin notes about this user
    
    # Relationships
    sessions = relationship("AdminSession", back_populates="admin_user", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        """Initialize admin user"""
        super().__init__()
        
        # Set default values
        if 'is_active' not in kwargs:
            kwargs['is_active'] = True
        if 'is_superuser' not in kwargs:
            kwargs['is_superuser'] = False
        if 'login_count' not in kwargs:
            kwargs['login_count'] = 0
        
        # Set attributes (password will be hashed separately)
        for key, value in kwargs.items():
            if hasattr(self, key) and key != 'password':
                setattr(self, key, value)
        
        # Hash password if provided
        if 'password' in kwargs:
            self.set_password(kwargs['password'])
    
    def set_password(self, password: str):
        """Hash and set the admin password"""
        if not password:
            raise ValueError("Password cannot be empty")
        
        # Generate salt and hash password
        salt = secrets.token_hex(16)
        password_with_salt = f"{password}{salt}"
        hash_obj = hashlib.sha256(password_with_salt.encode())
        self.password_hash = f"{salt}:{hash_obj.hexdigest()}"
    
    def check_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        if not self.password_hash or not password:
            return False
        
        try:
            salt, stored_hash = self.password_hash.split(':', 1)
            password_with_salt = f"{password}{salt}"
            hash_obj = hashlib.sha256(password_with_salt.encode())
            return hash_obj.hexdigest() == stored_hash
        except ValueError:
            return False
    
    def generate_password_reset_token(self) -> str:
        """Generate password reset token with expiration"""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=24)
        return self.password_reset_token
    
    def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using valid token"""
        if (self.password_reset_token == token and 
            self.password_reset_expires and 
            datetime.utcnow() < self.password_reset_expires):
            
            self.set_password(new_password)
            self.password_reset_token = None
            self.password_reset_expires = None
            return True
        return False
    
    def record_login(self):
        """Record successful login"""
        self.last_login = datetime.utcnow()
        self.login_count = (self.login_count or 0) + 1
    
    @property
    def full_name(self) -> str:
        """Get admin's full name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_active_session(self) -> Optional['AdminSession']:
        """Get current active session if any"""
        current_time = datetime.utcnow()
        for session in self.sessions:
            if session.expires_at > current_time and session.is_active:
                return session
        return None
    
    def validate(self) -> Dict[str, List[str]]:
        """Validate admin user data"""
        errors = super().validate()
        
        # Username validation
        if self.username and len(self.username.strip()) < 3:
            if 'username' not in errors:
                errors['username'] = []
            errors['username'].append("Username must be at least 3 characters")
        
        # Email validation
        if self.email and not self._is_valid_email(self.email):
            if 'email' not in errors:
                errors['email'] = []
            errors['email'].append("Invalid email format")
        
        return errors
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def to_dict(self, exclude_fields: List[str] = None) -> Dict[str, Any]:
        """Convert to dictionary, excluding sensitive information"""
        exclude_fields = exclude_fields or []
        exclude_fields.extend(['password_hash', 'password_reset_token'])
        
        data = super().to_dict(exclude_fields)
        data.update({
            'full_name': self.full_name,
            'has_active_session': self.get_active_session() is not None
        })
        return data


class AdminSession(BaseModel):
    """Admin session management for authentication tracking"""
    
    __tablename__ = 'admin_sessions'
    
    admin_user_id = Column(Integer, ForeignKey('admin_users.id'), nullable=False, index=True)
    session_token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Session metadata
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    login_method = Column(String(50), default='web')
    
    # Relationships
    admin_user = relationship("AdminUser", back_populates="sessions")
    
    def __init__(self, admin_user_id: int, duration_hours: int = 8, **kwargs):
        """Initialize admin session with automatic token generation"""
        super().__init__()
        
        self.admin_user_id = admin_user_id
        self.session_token = self._generate_session_token()
        self.expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
        self.is_active = True
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def _generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)
    
    def is_valid(self) -> bool:
        """Check if session is still valid"""
        return (
            self.is_active and 
            self.expires_at > datetime.utcnow()
        )
    
    def refresh(self, duration_hours: int = 8):
        """Refresh session expiration"""
        self.expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
    
    def invalidate(self):
        """Invalidate session"""
        self.is_active = False


class ConfigSetting(BaseModel):
    """System configuration settings"""
    
    __tablename__ = 'config_settings'
    
    key = Column(String(100), nullable=False, unique=True, index=True)
    value = Column(Text)
    data_type = Column(String(20), default='string')  # string, integer, float, boolean, json
    description = Column(Text)
    category = Column(String(50), default='general')
    is_sensitive = Column(Boolean, default=False)  # For passwords, API keys, etc.
    
    # Default and validation
    default_value = Column(Text)
    validation_regex = Column(String(500))
    allowed_values = Column(Text)  # JSON array of allowed values
    
    def __init__(self, **kwargs):
        super().__init__()
        
        if 'data_type' not in kwargs:
            kwargs['data_type'] = 'string'
        if 'category' not in kwargs:
            kwargs['category'] = 'general'
        if 'is_sensitive' not in kwargs:
            kwargs['is_sensitive'] = False
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_typed_value(self) -> Any:
        """Get value converted to appropriate type"""
        if self.value is None:
            return self.get_default_value()
        
        if self.data_type == 'integer':
            try:
                return int(self.value)
            except (ValueError, TypeError):
                return 0
        elif self.data_type == 'float':
            try:
                return float(self.value)
            except (ValueError, TypeError):
                return 0.0
        elif self.data_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.data_type == 'json':
            try:
                return json.loads(self.value)
            except json.JSONDecodeError:
                return {}
        else:
            return self.value
    
    def set_typed_value(self, value: Any):
        """Set value with automatic type conversion"""
        if self.data_type == 'json':
            self.value = json.dumps(value)
        else:
            self.value = str(value)
    
    def get_default_value(self) -> Any:
        """Get default value with type conversion"""
        if self.default_value is None:
            return None
        
        if self.data_type == 'integer':
            try:
                return int(self.default_value)
            except (ValueError, TypeError):
                return 0
        elif self.data_type == 'float':
            try:
                return float(self.default_value)
            except (ValueError, TypeError):
                return 0.0
        elif self.data_type == 'boolean':
            return self.default_value.lower() in ('true', '1', 'yes', 'on')
        elif self.data_type == 'json':
            try:
                return json.loads(self.default_value)
            except json.JSONDecodeError:
                return {}
        else:
            return self.default_value
    
    def get_allowed_values(self) -> List[str]:
        """Get list of allowed values"""
        if self.allowed_values:
            try:
                return json.loads(self.allowed_values)
            except json.JSONDecodeError:
                return []
        return []
    
    def set_allowed_values(self, values: List[str]):
        """Set allowed values"""
        self.allowed_values = json.dumps(values)
    
    def validate_value(self, value: Any) -> bool:
        """Validate value against constraints"""
        # Check allowed values
        allowed = self.get_allowed_values()
        if allowed and str(value) not in allowed:
            return False
        
        # Check regex validation
        if self.validation_regex and isinstance(value, str):
            import re
            if not re.match(self.validation_regex, value):
                return False
        
        return True
    
    @classmethod
    def get_setting(cls, session, key: str, default=None):
        """Get setting value by key"""
        setting = session.query(cls).filter(cls.key == key).first()
        if setting:
            return setting.get_typed_value()
        return default
    
    @classmethod
    def set_setting(cls, session, key: str, value: Any, description: str = None):
        """Set setting value by key"""
        setting = session.query(cls).filter(cls.key == key).first()
        if setting:
            setting.set_typed_value(value)
        else:
            setting = cls(key=key, description=description)
            setting.set_typed_value(value)
            session.add(setting)
        return setting


class EmailTemplate(BaseModel):
    """Email templates for various notifications"""
    
    __tablename__ = 'email_templates'
    
    name = Column(String(100), nullable=False, unique=True, index=True)
    subject = Column(String(300), nullable=False)
    html_content = Column(Text, nullable=False)
    text_content = Column(Text)
    
    # Template metadata
    description = Column(Text)
    category = Column(String(50), default='general')
    variables = Column(Text)  # JSON array of available variables
    is_active = Column(Boolean, default=True)
    
    def get_variables(self) -> List[str]:
        """Get list of available template variables"""
        if self.variables:
            try:
                return json.loads(self.variables)
            except json.JSONDecodeError:
                return []
        return []
    
    def set_variables(self, variables: List[str]):
        """Set template variables"""
        self.variables = json.dumps(variables)
    
    def render(self, variables: Dict[str, Any]) -> Dict[str, str]:
        """Render template with provided variables"""
        rendered_subject = self.subject
        rendered_html = self.html_content
        rendered_text = self.text_content or ""
        
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            rendered_subject = rendered_subject.replace(placeholder, str(value))
            rendered_html = rendered_html.replace(placeholder, str(value))
            rendered_text = rendered_text.replace(placeholder, str(value))
        
        return {
            'subject': rendered_subject,
            'html_content': rendered_html,
            'text_content': rendered_text
        }


# Create default configuration settings
DEFAULT_CONFIG_SETTINGS = [
    {
        'key': 'site_name',
        'value': 'AgentShop',
        'description': 'Name of the website',
        'category': 'general'
    },
    {
        'key': 'site_email',
        'value': 'admin@agentshop.com',
        'description': 'Main contact email address',
        'category': 'general'
    },
    {
        'key': 'admin_email',
        'value': 'admin@agentshop.com',
        'description': 'Admin email for notifications',
        'category': 'admin'
    },
    {
        'key': 'smtp_host',
        'value': 'localhost',
        'description': 'SMTP server hostname',
        'category': 'email'
    },
    {
        'key': 'smtp_port',
        'value': '587',
        'data_type': 'integer',
        'description': 'SMTP server port',
        'category': 'email'
    },
    {
        'key': 'smtp_username',
        'value': '',
        'description': 'SMTP username',
        'category': 'email',
        'is_sensitive': True
    },
    {
        'key': 'smtp_password',
        'value': '',
        'description': 'SMTP password',
        'category': 'email',
        'is_sensitive': True
    },
    {
        'key': 'stripe_public_key',
        'value': '',
        'description': 'Stripe publishable key',
        'category': 'payment',
        'is_sensitive': True
    },
    {
        'key': 'stripe_secret_key',
        'value': '',
        'description': 'Stripe secret key',
        'category': 'payment',
        'is_sensitive': True
    },
    {
        'key': 'paypal_client_id',
        'value': '',
        'description': 'PayPal client ID',
        'category': 'payment',
        'is_sensitive': True
    },
    {
        'key': 'paypal_client_secret',
        'value': '',
        'description': 'PayPal client secret',
        'category': 'payment',
        'is_sensitive': True
    },
    {
        'key': 'tax_rate',
        'value': '0.0',
        'data_type': 'float',
        'description': 'Default tax rate (as decimal)',
        'category': 'payment'
    },
    {
        'key': 'download_link_expiry_hours',
        'value': '48',
        'data_type': 'integer',
        'description': 'Hours before download links expire',
        'category': 'downloads'
    },
    {
        'key': 'max_downloads_per_purchase',
        'value': '5',
        'data_type': 'integer',
        'description': 'Maximum downloads allowed per purchase',
        'category': 'downloads'
    }
]


def create_default_settings(session):
    """Create default configuration settings if they don't exist"""
    for setting_data in DEFAULT_CONFIG_SETTINGS:
        existing = session.query(ConfigSetting).filter(
            ConfigSetting.key == setting_data['key']
        ).first()
        
        if not existing:
            setting = ConfigSetting(**setting_data)
            session.add(setting)
    
    session.commit()


# Import foreign key references
from sqlalchemy import ForeignKey