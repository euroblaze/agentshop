#!/usr/bin/env python3
"""
Customer Service - Business logic for customer management
Handles customer accounts, authentication, sessions, and support requests
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from .base_service import BaseService, ValidationError, ServiceError
from ..repositories.customer_repository import (
    CustomerRepository, CustomerSessionRepository, SupportRequestRepository
)
from ..models.customer_models import Customer, CustomerSession, SupportRequest

logger = logging.getLogger(__name__)


class CustomerService(BaseService[Customer]):
    """Service for Customer entity with authentication and account management"""
    
    def __init__(self, repository: CustomerRepository = None, session: Session = None):
        super().__init__(repository, session)
        self.session_service = CustomerSessionService(session=session)
    
    def _create_repository(self) -> CustomerRepository:
        """Create CustomerRepository instance"""
        return CustomerRepository(self._session)
    
    def _create_entity_from_data(self, entity_data: Dict[str, Any]) -> Customer:
        """Create Customer instance from data dictionary"""
        return Customer(**entity_data)
    
    def _validate_business_rules(self, customer: Customer,
                                is_create: bool = True) -> Dict[str, List[str]]:
        """Validate customer business rules"""
        errors = {}
        
        # Email uniqueness check
        if is_create or customer.email:
            if self.repository.email_exists(customer.email, customer.id if not is_create else None):
                errors['email'] = ['Email address already registered']
        
        # Password strength validation (for new customers)
        if is_create and hasattr(customer, '_plain_password'):
            password_errors = self._validate_password_strength(customer._plain_password)
            if password_errors:
                errors['password'] = password_errors
        
        return errors
    
    def _apply_create_business_rules(self, customer: Customer, entity_data: Dict[str, Any]):
        """Apply business rules during customer creation"""
        # Set default values
        customer.is_active = True
        customer.email_verified = False
        customer.login_count = 0
        
        # Store registration metadata
        customer.registration_ip = entity_data.get('ip_address')
        customer.user_agent = entity_data.get('user_agent')
        customer.referral_source = entity_data.get('referral_source')
        
        # Generate email verification token
        customer.generate_email_verification_token()
    
    def _after_create(self, customer: Customer, entity_data: Dict[str, Any]):
        """Send welcome email and verification after customer creation"""
        try:
            # TODO: Send welcome email with verification link
            logger.info(f"Customer registered: {customer.email}")
        except Exception as e:
            logger.error(f"Error sending welcome email: {e}")
    
    def _get_default_filters(self) -> Dict[str, Any]:
        """Get default filters for customer queries"""
        return {'is_deleted': 'N'}
    
    def _get_default_search_fields(self) -> List[str]:
        """Get default search fields for customers"""
        return ['first_name', 'last_name', 'email']
    
    # Authentication and Account Management
    
    def register_customer(self, email: str, password: str, first_name: str,
                         last_name: str, ip_address: str = None,
                         user_agent: str = None, **additional_data) -> Customer:
        """
        Register new customer account
        
        Args:
            email: Customer email address
            password: Plain text password
            first_name: Customer first name
            last_name: Customer last name
            ip_address: Registration IP address
            user_agent: Registration user agent
            **additional_data: Additional customer data
            
        Returns:
            Created customer instance
            
        Raises:
            ValidationError: If registration data is invalid
            ServiceError: If registration fails
        """
        try:
            # Prepare customer data
            customer_data = {
                'email': email.lower().strip(),
                'first_name': first_name.strip(),
                'last_name': last_name.strip(),
                'ip_address': ip_address,
                'user_agent': user_agent,
                **additional_data
            }
            
            # Store password for validation
            customer_data['_plain_password'] = password
            
            # Create customer
            customer = self.create(customer_data)
            
            # Set password (will be hashed)
            customer.set_password(password)
            self.repository.update(customer)
            
            return customer
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error registering customer: {e}")
            raise ServiceError("Registration failed") from e
    
    def authenticate_customer(self, email: str, password: str,
                            ip_address: str = None, user_agent: str = None) -> Optional[Tuple[Customer, CustomerSession]]:
        """
        Authenticate customer and create session
        
        Args:
            email: Customer email address
            password: Plain text password
            ip_address: Login IP address
            user_agent: Login user agent
            
        Returns:
            Tuple of (Customer, CustomerSession) if successful, None otherwise
        """
        try:
            # Authenticate customer
            customer = self.repository.authenticate_customer(email, password)
            if not customer:
                return None
            
            # Create session
            session = self.session_service.create_session(
                customer.id, ip_address=ip_address, user_agent=user_agent
            )
            
            return customer, session
            
        except Exception as e:
            logger.error(f"Error authenticating customer: {e}")
            return None
    
    def logout_customer(self, session_token: str) -> bool:
        """
        Logout customer by invalidating session
        
        Args:
            session_token: Session token to invalidate
            
        Returns:
            True if successful
        """
        try:
            return self.session_service.invalidate_session(session_token)
        except Exception as e:
            logger.error(f"Error logging out customer: {e}")
            return False
    
    def get_customer_by_session(self, session_token: str) -> Optional[Customer]:
        """
        Get customer by valid session token
        
        Args:
            session_token: Session token
            
        Returns:
            Customer instance if session is valid, None otherwise
        """
        try:
            session = self.session_service.get_valid_session(session_token)
            if session:
                return self.get_by_id(session.customer_id)
            return None
        except Exception as e:
            logger.error(f"Error getting customer by session: {e}")
            return None
    
    def verify_email(self, customer_id: int, verification_token: str) -> bool:
        """
        Verify customer email address
        
        Args:
            customer_id: Customer ID
            verification_token: Email verification token
            
        Returns:
            True if verification successful
        """
        try:
            customer = self.get_by_id(customer_id)
            if customer and customer.verify_email(verification_token):
                self.repository.update(customer)
                logger.info(f"Email verified for customer: {customer.email}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error verifying email: {e}")
            return False
    
    def request_password_reset(self, email: str) -> bool:
        """
        Request password reset for customer
        
        Args:
            email: Customer email address
            
        Returns:
            True if reset token generated (even if email doesn't exist for security)
        """
        try:
            customer = self.repository.get_by_email(email)
            if customer and customer.is_active:
                customer.generate_password_reset_token()
                self.repository.update(customer)
                
                # TODO: Send password reset email
                logger.info(f"Password reset requested for: {email}")
            
            # Always return True for security (don't reveal if email exists)
            return True
        except Exception as e:
            logger.error(f"Error requesting password reset: {e}")
            return False
    
    def reset_password(self, customer_id: int, reset_token: str, 
                      new_password: str) -> bool:
        """
        Reset customer password using reset token
        
        Args:
            customer_id: Customer ID
            reset_token: Password reset token
            new_password: New plain text password
            
        Returns:
            True if password reset successful
        """
        try:
            # Validate password strength
            password_errors = self._validate_password_strength(new_password)
            if password_errors:
                raise ValidationError("Invalid password", {'password': password_errors})
            
            customer = self.get_by_id(customer_id)
            if customer and customer.reset_password(reset_token, new_password):
                self.repository.update(customer)
                
                # Invalidate all existing sessions for security
                self.session_service.invalidate_customer_sessions(customer_id)
                
                logger.info(f"Password reset for customer: {customer.email}")
                return True
            return False
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error resetting password: {e}")
            return False
    
    def update_profile(self, customer_id: int, profile_data: Dict[str, Any]) -> Optional[Customer]:
        """
        Update customer profile information
        
        Args:
            customer_id: Customer ID
            profile_data: Profile data to update
            
        Returns:
            Updated customer instance or None
        """
        try:
            # Exclude sensitive fields from profile updates
            excluded_fields = ['password_hash', 'email_verification_token', 'password_reset_token']
            filtered_data = {k: v for k, v in profile_data.items() if k not in excluded_fields}
            
            return self.update(customer_id, filtered_data)
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            return None
    
    def change_password(self, customer_id: int, current_password: str,
                       new_password: str) -> bool:
        """
        Change customer password
        
        Args:
            customer_id: Customer ID
            current_password: Current password for verification
            new_password: New password
            
        Returns:
            True if password changed successfully
        """
        try:
            customer = self.get_by_id(customer_id)
            if not customer or not customer.check_password(current_password):
                raise ValidationError("Current password is incorrect")
            
            # Validate new password strength
            password_errors = self._validate_password_strength(new_password)
            if password_errors:
                raise ValidationError("Invalid new password", {'password': password_errors})
            
            customer.set_password(new_password)
            self.repository.update(customer)
            
            # Invalidate other sessions for security
            active_sessions = self.session_service.get_customer_sessions(customer_id, active_only=True)
            for session in active_sessions[1:]:  # Keep current session
                self.session_service.invalidate_session(session.session_token)
            
            logger.info(f"Password changed for customer: {customer.email}")
            return True
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            return False
    
    def deactivate_account(self, customer_id: int, reason: str = None) -> bool:
        """
        Deactivate customer account
        
        Args:
            customer_id: Customer ID
            reason: Optional reason for deactivation
            
        Returns:
            True if successful
        """
        try:
            customer = self.get_by_id(customer_id)
            if customer:
                customer.is_active = False
                self.repository.update(customer)
                
                # Invalidate all sessions
                self.session_service.invalidate_customer_sessions(customer_id)
                
                logger.info(f"Customer account deactivated: {customer.email}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deactivating account: {e}")
            return False
    
    # Administrative functions
    
    def get_customer_stats(self) -> Dict[str, Any]:
        """Get customer statistics"""
        try:
            return self.repository.get_customer_stats()
        except Exception as e:
            logger.error(f"Error getting customer stats: {e}")
            return {}
    
    def search_customers(self, search_term: str, limit: int = 50) -> List[Customer]:
        """Search customers for admin"""
        try:
            return self.repository.search_customers(search_term, limit)
        except Exception as e:
            logger.error(f"Error searching customers: {e}")
            return []
    
    def get_recent_customers(self, days: int = 30, limit: int = 10) -> List[Customer]:
        """Get recently registered customers"""
        try:
            return self.repository.get_recent_customers(days, limit)
        except Exception as e:
            logger.error(f"Error getting recent customers: {e}")
            return []
    
    # Helper methods
    
    def _validate_password_strength(self, password: str) -> List[str]:
        """Validate password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        # Check for common weak passwords
        weak_passwords = ['password', '12345678', 'qwerty', 'abc123']
        if password.lower() in weak_passwords:
            errors.append("Password is too common")
        
        return errors


class CustomerSessionService(BaseService[CustomerSession]):
    """Service for CustomerSession entity"""
    
    def __init__(self, repository: CustomerSessionRepository = None, session: Session = None):
        super().__init__(repository, session)
    
    def _create_repository(self) -> CustomerSessionRepository:
        """Create CustomerSessionRepository instance"""
        return CustomerSessionRepository(self._session)
    
    def _create_entity_from_data(self, entity_data: Dict[str, Any]) -> CustomerSession:
        """Create CustomerSession instance from data dictionary"""
        return CustomerSession(**entity_data)
    
    def create_session(self, customer_id: int, duration_hours: int = 24,
                      ip_address: str = None, user_agent: str = None) -> CustomerSession:
        """Create new customer session"""
        try:
            return self.repository.create_session(
                customer_id, duration_hours, ip_address, user_agent
            )
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise ServiceError("Failed to create session") from e
    
    def get_valid_session(self, session_token: str) -> Optional[CustomerSession]:
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
    
    def invalidate_customer_sessions(self, customer_id: int) -> int:
        """Invalidate all sessions for a customer"""
        try:
            return self.repository.invalidate_customer_sessions(customer_id)
        except Exception as e:
            logger.error(f"Error invalidating customer sessions: {e}")
            return 0
    
    def get_customer_sessions(self, customer_id: int, active_only: bool = True) -> List[CustomerSession]:
        """Get sessions for a customer"""
        try:
            return self.repository.get_customer_sessions(customer_id, active_only)
        except Exception as e:
            logger.error(f"Error getting customer sessions: {e}")
            return []
    
    def refresh_session(self, session_token: str, duration_hours: int = 24) -> bool:
        """Refresh session expiration"""
        try:
            return self.repository.refresh_session(session_token, duration_hours)
        except Exception as e:
            logger.error(f"Error refreshing session: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        try:
            return self.repository.cleanup_expired_sessions()
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0


class SupportRequestService(BaseService[SupportRequest]):
    """Service for SupportRequest entity"""
    
    def __init__(self, repository: SupportRequestRepository = None, session: Session = None):
        super().__init__(repository, session)
    
    def _create_repository(self) -> SupportRequestRepository:
        """Create SupportRequestRepository instance"""
        return SupportRequestRepository(self._session)
    
    def _create_entity_from_data(self, entity_data: Dict[str, Any]) -> SupportRequest:
        """Create SupportRequest instance from data dictionary"""
        return SupportRequest(**entity_data)
    
    def _after_create(self, support_request: SupportRequest, entity_data: Dict[str, Any]):
        """Send notification after support request creation"""
        try:
            # TODO: Send notification email to admin
            logger.info(f"New support request created: {support_request.id}")
        except Exception as e:
            logger.error(f"Error sending support request notification: {e}")
    
    def create_support_request(self, customer_id: int, subject: str, message: str,
                              request_type: str = 'support', order_id: int = None,
                              priority: str = 'normal') -> SupportRequest:
        """Create new support request"""
        try:
            return self.repository.create_support_request(
                customer_id, subject, message, request_type, order_id, priority
            )
        except Exception as e:
            logger.error(f"Error creating support request: {e}")
            raise ServiceError("Failed to create support request") from e
    
    def get_customer_requests(self, customer_id: int, status: str = None) -> List[SupportRequest]:
        """Get support requests for a customer"""
        try:
            return self.repository.get_customer_requests(customer_id, status)
        except Exception as e:
            logger.error(f"Error getting customer requests: {e}")
            return []
    
    def get_open_requests(self, priority: str = None) -> List[SupportRequest]:
        """Get open support requests for admin"""
        try:
            return self.repository.get_open_requests(priority)
        except Exception as e:
            logger.error(f"Error getting open requests: {e}")
            return []
    
    def resolve_request(self, request_id: int, admin_user: str, response: str) -> bool:
        """Resolve support request"""
        try:
            success = self.repository.resolve_request(request_id, admin_user, response)
            if success:
                # TODO: Send resolution email to customer
                logger.info(f"Support request resolved: {request_id}")
            return success
        except Exception as e:
            logger.error(f"Error resolving request: {e}")
            return False
    
    def update_request_status(self, request_id: int, status: str) -> bool:
        """Update support request status"""
        try:
            return self.repository.update_status(request_id, status)
        except Exception as e:
            logger.error(f"Error updating request status: {e}")
            return False
    
    def get_request_stats(self) -> Dict[str, Any]:
        """Get support request statistics"""
        try:
            return self.repository.get_request_stats()
        except Exception as e:
            logger.error(f"Error getting request stats: {e}")
            return {}