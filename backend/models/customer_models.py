#!/usr/bin/env python3
"""
Customer Models - Database models for customer management
Handles customer accounts, authentication, sessions, and profile management
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from typing import Dict, Any, List, Optional
import hashlib
import secrets
from datetime import datetime, timedelta
import re

try:
    from ..core.orm.base_model import BaseModel, SoftDeleteMixin
except ImportError:
    from core.orm.base_model import BaseModel, SoftDeleteMixin


class Customer(BaseModel, SoftDeleteMixin):
    """Customer account model for user registration and management"""
    
    __tablename__ = 'customers'
    
    # Authentication fields
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255), nullable=True)
    
    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    
    # Address information
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100))
    
    # Account status and tracking
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    
    # Password reset functionality
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    
    # Marketing preferences
    email_marketing = Column(Boolean, default=False)
    sms_marketing = Column(Boolean, default=False)
    
    # Customer metadata
    registration_ip = Column(String(45))
    user_agent = Column(String(500))
    referral_source = Column(String(200))
    
    # Relationships
    sessions = relationship("CustomerSession", back_populates="customer", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="customer")
    reviews = relationship("ProductReview", back_populates="customer")
    inquiries = relationship("ProductInquiry", back_populates="customer")
    support_requests = relationship("SupportRequest", back_populates="customer")
    
    def __init__(self, **kwargs):
        """Initialize customer with validation"""
        super().__init__()
        
        # Set default values
        if 'is_active' not in kwargs:
            kwargs['is_active'] = True
        if 'email_verified' not in kwargs:
            kwargs['email_verified'] = False
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
        """Hash and set the customer password"""
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
    
    def generate_email_verification_token(self) -> str:
        """Generate email verification token"""
        self.email_verification_token = secrets.token_urlsafe(32)
        return self.email_verification_token
    
    def verify_email(self, token: str) -> bool:
        """Verify email using provided token"""
        if self.email_verification_token == token:
            self.email_verified = True
            self.email_verification_token = None
            return True
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
        """Get customer's full name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def full_address(self) -> str:
        """Get formatted full address"""
        address_parts = []
        
        if self.address_line1:
            address_parts.append(self.address_line1)
        if self.address_line2:
            address_parts.append(self.address_line2)
        if self.city:
            address_parts.append(self.city)
        if self.state:
            address_parts.append(self.state)
        if self.postal_code:
            address_parts.append(self.postal_code)
        if self.country:
            address_parts.append(self.country)
        
        return ', '.join(address_parts)
    
    def get_active_session(self) -> Optional['CustomerSession']:
        """Get current active session if any"""
        current_time = datetime.utcnow()
        for session in self.sessions:
            if session.expires_at > current_time and session.is_active:
                return session
        return None
    
    def validate(self) -> Dict[str, List[str]]:
        """Validate customer data"""
        errors = super().validate()
        
        # Email validation
        if self.email and not self._is_valid_email(self.email):
            if 'email' not in errors:
                errors['email'] = []
            errors['email'].append("Invalid email format")
        
        # Phone validation
        if self.phone and not self._is_valid_phone(self.phone):
            if 'phone' not in errors:
                errors['phone'] = []
            errors['phone'].append("Invalid phone number format")
        
        # Name validation
        if self.first_name and len(self.first_name.strip()) < 2:
            if 'first_name' not in errors:
                errors['first_name'] = []
            errors['first_name'].append("First name must be at least 2 characters")
        
        if self.last_name and len(self.last_name.strip()) < 2:
            if 'last_name' not in errors:
                errors['last_name'] = []
            errors['last_name'].append("Last name must be at least 2 characters")
        
        return errors
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Basic phone number validation"""
        # Remove common separators and check if remaining chars are digits
        cleaned = re.sub(r'[-\s\(\)\+\.]', '', phone)
        return cleaned.isdigit() and 7 <= len(cleaned) <= 15
    
    def to_dict(self, exclude_fields: List[str] = None) -> Dict[str, Any]:
        """Convert to dictionary, excluding sensitive information"""
        exclude_fields = exclude_fields or []
        exclude_fields.extend(['password_hash', 'password_reset_token', 'email_verification_token'])
        
        data = super().to_dict(exclude_fields)
        data.update({
            'full_name': self.full_name,
            'full_address': self.full_address,
            'has_active_session': self.get_active_session() is not None
        })
        return data


class CustomerSession(BaseModel):
    """Customer session management for authentication tracking"""
    
    __tablename__ = 'customer_sessions'
    
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False, index=True)
    session_token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Session metadata
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    login_method = Column(String(50), default='web')  # web, mobile, api
    
    # Relationships
    customer = relationship("Customer", back_populates="sessions")
    
    def __init__(self, customer_id: int, duration_hours: int = 24, **kwargs):
        """Initialize session with automatic token generation"""
        super().__init__()
        
        self.customer_id = customer_id
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
    
    def refresh(self, duration_hours: int = 24):
        """Refresh session expiration"""
        self.expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
    
    def invalidate(self):
        """Invalidate session"""
        self.is_active = False
    
    @classmethod
    def cleanup_expired(cls, session):
        """Remove expired sessions from database"""
        current_time = datetime.utcnow()
        expired_sessions = session.query(cls).filter(
            cls.expires_at < current_time
        ).all()
        
        for expired_session in expired_sessions:
            session.delete(expired_session)
        
        return len(expired_sessions)


class SupportRequest(BaseModel):
    """Customer support requests and returns"""
    
    __tablename__ = 'support_requests'
    
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=True, index=True)
    
    # Request details
    type = Column(String(50), nullable=False)  # support, return, refund, technical
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Status tracking
    status = Column(String(20), default='open')  # open, in_progress, resolved, closed
    priority = Column(String(20), default='normal')  # low, normal, high, urgent
    
    # Response handling
    admin_response = Column(Text)
    resolved_at = Column(DateTime)
    resolved_by = Column(String(100))  # Admin user who resolved
    
    # File attachments
    attachments = Column(Text)  # JSON array of file paths
    
    # Relationships
    customer = relationship("Customer", back_populates="support_requests")
    order = relationship("Order", back_populates="support_requests")
    
    def get_attachments(self) -> List[str]:
        """Get list of attachment file paths"""
        if self.attachments:
            try:
                import json
                return json.loads(self.attachments)
            except json.JSONDecodeError:
                return []
        return []
    
    def set_attachments(self, file_paths: List[str]):
        """Set attachments from list of file paths"""
        import json
        self.attachments = json.dumps(file_paths)
    
    def resolve(self, admin_user: str, response: str):
        """Mark support request as resolved"""
        self.status = 'resolved'
        self.admin_response = response
        self.resolved_at = datetime.utcnow()
        self.resolved_by = admin_user
    
    def validate(self) -> Dict[str, List[str]]:
        """Validate support request data"""
        errors = super().validate()
        
        if self.type not in ['support', 'return', 'refund', 'technical']:
            if 'type' not in errors:
                errors['type'] = []
            errors['type'].append("Invalid support request type")
        
        if self.status not in ['open', 'in_progress', 'resolved', 'closed']:
            if 'status' not in errors:
                errors['status'] = []
            errors['status'].append("Invalid status")
        
        if self.priority not in ['low', 'normal', 'high', 'urgent']:
            if 'priority' not in errors:
                errors['priority'] = []
            errors['priority'].append("Invalid priority level")
        
        return errors


# Import references for relationships (avoid circular imports)
from .order_models import Order
from .product_models import ProductReview, ProductInquiry