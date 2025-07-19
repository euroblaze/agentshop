#!/usr/bin/env python3
"""
Customer Repository - Data access layer for customer-related operations
Provides specialized queries and operations for customers, sessions, and support requests
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta

from core.repositories.base_repository import BaseRepository
from ..models.customer_models import Customer, CustomerSession, SupportRequest


class CustomerRepository(BaseRepository[Customer]):
    """Repository for Customer entities with specialized customer operations"""
    
    def __init__(self, session: Session = None):
        super().__init__(Customer, session)
    
    def get_by_email(self, email: str) -> Optional[Customer]:
        """
        Get customer by email address
        
        Args:
            email: Customer email address
            
        Returns:
            Customer instance or None
        """
        return self.session.query(Customer).filter(
            and_(
                Customer.email == email.lower(),
                Customer.is_deleted != 'Y'
            )
        ).first()
    
    def email_exists(self, email: str, exclude_customer_id: int = None) -> bool:
        """
        Check if email address is already registered
        
        Args:
            email: Email address to check
            exclude_customer_id: Optional customer ID to exclude from check
            
        Returns:
            True if email exists
        """
        query = self.session.query(Customer).filter(
            and_(
                Customer.email == email.lower(),
                Customer.is_deleted != 'Y'
            )
        )
        
        if exclude_customer_id:
            query = query.filter(Customer.id != exclude_customer_id)
        
        return query.first() is not None
    
    def create_customer(self, email: str, password: str, first_name: str, 
                       last_name: str, **kwargs) -> Customer:
        """
        Create a new customer account
        
        Args:
            email: Customer email address
            password: Plain text password (will be hashed)
            first_name: Customer first name
            last_name: Customer last name
            **kwargs: Additional customer fields
            
        Returns:
            Created customer instance
            
        Raises:
            ValueError: If email already exists
        """
        if self.email_exists(email):
            raise ValueError("Email address already registered")
        
        customer = Customer(
            email=email.lower(),
            first_name=first_name,
            last_name=last_name,
            **kwargs
        )
        customer.set_password(password)
        
        return self.create(customer)
    
    def authenticate_customer(self, email: str, password: str) -> Optional[Customer]:
        """
        Authenticate customer credentials
        
        Args:
            email: Customer email address
            password: Plain text password
            
        Returns:
            Customer instance if authentication successful, None otherwise
        """
        customer = self.get_by_email(email)
        if customer and customer.is_active and customer.check_password(password):
            customer.record_login()
            return customer
        return None
    
    def get_active_customers(self, limit: int = None, offset: int = None) -> List[Customer]:
        """
        Get all active customers
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of active customers
        """
        query = self.session.query(Customer).filter(
            and_(
                Customer.is_active == True,
                Customer.is_deleted != 'Y'
            )
        ).order_by(desc(Customer.created_at))
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def search_customers(self, search_term: str, limit: int = 50) -> List[Customer]:
        """
        Search customers by name or email
        
        Args:
            search_term: Text to search for
            limit: Maximum number of results
            
        Returns:
            List of matching customers
        """
        if not search_term:
            return []
        
        search_conditions = or_(
            Customer.first_name.ilike(f"%{search_term}%"),
            Customer.last_name.ilike(f"%{search_term}%"),
            Customer.email.ilike(f"%{search_term}%")
        )
        
        return self.session.query(Customer).filter(
            and_(
                search_conditions,
                Customer.is_deleted != 'Y'
            )
        ).order_by(Customer.first_name, Customer.last_name).limit(limit).all()
    
    def get_customers_by_registration_date(self, start_date: datetime, 
                                          end_date: datetime = None) -> List[Customer]:
        """
        Get customers registered within date range
        
        Args:
            start_date: Start of date range
            end_date: End of date range (defaults to now)
            
        Returns:
            List of customers registered in date range
        """
        if end_date is None:
            end_date = datetime.utcnow()
        
        return self.session.query(Customer).filter(
            and_(
                Customer.created_at >= start_date,
                Customer.created_at <= end_date,
                Customer.is_deleted != 'Y'
            )
        ).order_by(desc(Customer.created_at)).all()
    
    def get_recent_customers(self, days: int = 30, limit: int = 10) -> List[Customer]:
        """
        Get recently registered customers
        
        Args:
            days: Number of days back to look
            limit: Maximum number of customers
            
        Returns:
            List of recent customers
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.get_customers_by_registration_date(cutoff_date)[:limit]
    
    def update_last_login(self, customer_id: int) -> bool:
        """
        Update customer's last login timestamp
        
        Args:
            customer_id: Customer ID
            
        Returns:
            True if successful
        """
        try:
            self.session.query(Customer).filter(
                Customer.id == customer_id
            ).update({
                Customer.last_login: datetime.utcnow(),
                Customer.login_count: Customer.login_count + 1
            })
            return True
        except Exception:
            return False
    
    def deactivate_customer(self, customer_id: int, reason: str = None) -> bool:
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
                if reason:
                    # Could add a notes field for tracking reasons
                    pass
                return True
        except Exception:
            return False
        
        return False
    
    def get_customer_stats(self) -> Dict[str, Any]:
        """
        Get customer statistics
        
        Returns:
            Dictionary with customer statistics
        """
        try:
            total_customers = self.session.query(func.count(Customer.id)).filter(
                Customer.is_deleted != 'Y'
            ).scalar()
            
            active_customers = self.session.query(func.count(Customer.id)).filter(
                and_(
                    Customer.is_active == True,
                    Customer.is_deleted != 'Y'
                )
            ).scalar()
            
            # Customers registered in last 30 days
            recent_cutoff = datetime.utcnow() - timedelta(days=30)
            recent_customers = self.session.query(func.count(Customer.id)).filter(
                and_(
                    Customer.created_at >= recent_cutoff,
                    Customer.is_deleted != 'Y'
                )
            ).scalar()
            
            # Customers with verified emails
            verified_customers = self.session.query(func.count(Customer.id)).filter(
                and_(
                    Customer.email_verified == True,
                    Customer.is_deleted != 'Y'
                )
            ).scalar()
            
            return {
                'total_customers': total_customers or 0,
                'active_customers': active_customers or 0,
                'recent_customers': recent_customers or 0,
                'verified_customers': verified_customers or 0,
                'verification_rate': (verified_customers / total_customers * 100) if total_customers > 0 else 0
            }
        except Exception:
            return {
                'total_customers': 0,
                'active_customers': 0,
                'recent_customers': 0,
                'verified_customers': 0,
                'verification_rate': 0
            }


class CustomerSessionRepository(BaseRepository[CustomerSession]):
    """Repository for CustomerSession entities"""
    
    def __init__(self, session: Session = None):
        super().__init__(CustomerSession, session)
    
    def create_session(self, customer_id: int, duration_hours: int = 24, 
                      ip_address: str = None, user_agent: str = None) -> CustomerSession:
        """
        Create a new customer session
        
        Args:
            customer_id: Customer ID
            duration_hours: Session duration in hours
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Created session instance
        """
        session = CustomerSession(
            customer_id=customer_id,
            duration_hours=duration_hours,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return self.create(session)
    
    def get_by_token(self, session_token: str) -> Optional[CustomerSession]:
        """
        Get session by token
        
        Args:
            session_token: Session token
            
        Returns:
            CustomerSession instance or None
        """
        return self.session.query(CustomerSession).filter(
            CustomerSession.session_token == session_token
        ).first()
    
    def get_valid_session(self, session_token: str) -> Optional[CustomerSession]:
        """
        Get valid (non-expired, active) session by token
        
        Args:
            session_token: Session token
            
        Returns:
            Valid CustomerSession instance or None
        """
        session = self.get_by_token(session_token)
        if session and session.is_valid():
            return session
        return None
    
    def get_customer_sessions(self, customer_id: int, 
                            active_only: bool = True) -> List[CustomerSession]:
        """
        Get all sessions for a customer
        
        Args:
            customer_id: Customer ID
            active_only: Whether to return only active sessions
            
        Returns:
            List of customer sessions
        """
        query = self.session.query(CustomerSession).filter(
            CustomerSession.customer_id == customer_id
        )
        
        if active_only:
            current_time = datetime.utcnow()
            query = query.filter(
                and_(
                    CustomerSession.is_active == True,
                    CustomerSession.expires_at > current_time
                )
            )
        
        return query.order_by(desc(CustomerSession.created_at)).all()
    
    def invalidate_session(self, session_token: str) -> bool:
        """
        Invalidate a session
        
        Args:
            session_token: Session token to invalidate
            
        Returns:
            True if successful
        """
        try:
            self.session.query(CustomerSession).filter(
                CustomerSession.session_token == session_token
            ).update({
                CustomerSession.is_active: False
            })
            return True
        except Exception:
            return False
    
    def invalidate_customer_sessions(self, customer_id: int) -> int:
        """
        Invalidate all sessions for a customer
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Number of sessions invalidated
        """
        try:
            return self.session.query(CustomerSession).filter(
                and_(
                    CustomerSession.customer_id == customer_id,
                    CustomerSession.is_active == True
                )
            ).update({
                CustomerSession.is_active: False
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
        expired_sessions = self.session.query(CustomerSession).filter(
            CustomerSession.expires_at < current_time
        ).all()
        
        count = len(expired_sessions)
        for expired_session in expired_sessions:
            self.session.delete(expired_session)
        
        return count
    
    def refresh_session(self, session_token: str, duration_hours: int = 24) -> bool:
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
            self.session.query(CustomerSession).filter(
                CustomerSession.session_token == session_token
            ).update({
                CustomerSession.expires_at: new_expiry
            })
            return True
        except Exception:
            return False


class SupportRequestRepository(BaseRepository[SupportRequest]):
    """Repository for SupportRequest entities"""
    
    def __init__(self, session: Session = None):
        super().__init__(SupportRequest, session)
    
    def create_support_request(self, customer_id: int, subject: str, 
                              message: str, request_type: str = 'support',
                              order_id: int = None, priority: str = 'normal') -> SupportRequest:
        """
        Create a new support request
        
        Args:
            customer_id: Customer ID
            subject: Request subject
            message: Request message
            request_type: Type of request (support, return, refund, technical)
            order_id: Related order ID if applicable
            priority: Request priority (low, normal, high, urgent)
            
        Returns:
            Created support request instance
        """
        support_request = SupportRequest(
            customer_id=customer_id,
            order_id=order_id,
            type=request_type,
            subject=subject,
            message=message,
            priority=priority
        )
        
        return self.create(support_request)
    
    def get_customer_requests(self, customer_id: int, 
                            status: str = None) -> List[SupportRequest]:
        """
        Get support requests for a customer
        
        Args:
            customer_id: Customer ID
            status: Optional status filter
            
        Returns:
            List of customer support requests
        """
        query = self.session.query(SupportRequest).filter(
            SupportRequest.customer_id == customer_id
        )
        
        if status:
            query = query.filter(SupportRequest.status == status)
        
        return query.order_by(desc(SupportRequest.created_at)).all()
    
    def get_open_requests(self, priority: str = None) -> List[SupportRequest]:
        """
        Get all open support requests
        
        Args:
            priority: Optional priority filter
            
        Returns:
            List of open support requests
        """
        query = self.session.query(SupportRequest).filter(
            SupportRequest.status.in_(['open', 'in_progress'])
        )
        
        if priority:
            query = query.filter(SupportRequest.priority == priority)
        
        return query.order_by(
            SupportRequest.priority.desc(),
            SupportRequest.created_at
        ).all()
    
    def get_requests_by_type(self, request_type: str) -> List[SupportRequest]:
        """
        Get support requests by type
        
        Args:
            request_type: Request type (support, return, refund, technical)
            
        Returns:
            List of support requests
        """
        return self.session.query(SupportRequest).filter(
            SupportRequest.type == request_type
        ).order_by(desc(SupportRequest.created_at)).all()
    
    def resolve_request(self, request_id: int, admin_user: str, 
                       response: str) -> bool:
        """
        Resolve a support request
        
        Args:
            request_id: Support request ID
            admin_user: Admin user who resolved the request
            response: Admin response
            
        Returns:
            True if successful
        """
        try:
            request = self.get_by_id(request_id)
            if request:
                request.resolve(admin_user, response)
                return True
        except Exception:
            return False
        
        return False
    
    def update_status(self, request_id: int, status: str) -> bool:
        """
        Update support request status
        
        Args:
            request_id: Support request ID
            status: New status
            
        Returns:
            True if successful
        """
        try:
            self.session.query(SupportRequest).filter(
                SupportRequest.id == request_id
            ).update({
                SupportRequest.status: status
            })
            return True
        except Exception:
            return False
    
    def get_request_stats(self) -> Dict[str, Any]:
        """
        Get support request statistics
        
        Returns:
            Dictionary with support request statistics
        """
        try:
            total_requests = self.session.query(func.count(SupportRequest.id)).scalar()
            
            open_requests = self.session.query(func.count(SupportRequest.id)).filter(
                SupportRequest.status.in_(['open', 'in_progress'])
            ).scalar()
            
            resolved_requests = self.session.query(func.count(SupportRequest.id)).filter(
                SupportRequest.status == 'resolved'
            ).scalar()
            
            # Recent requests (last 7 days)
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            recent_requests = self.session.query(func.count(SupportRequest.id)).filter(
                SupportRequest.created_at >= recent_cutoff
            ).scalar()
            
            # High priority requests
            high_priority = self.session.query(func.count(SupportRequest.id)).filter(
                and_(
                    SupportRequest.priority.in_(['high', 'urgent']),
                    SupportRequest.status.in_(['open', 'in_progress'])
                )
            ).scalar()
            
            return {
                'total_requests': total_requests or 0,
                'open_requests': open_requests or 0,
                'resolved_requests': resolved_requests or 0,
                'recent_requests': recent_requests or 0,
                'high_priority_requests': high_priority or 0,
                'resolution_rate': (resolved_requests / total_requests * 100) if total_requests > 0 else 0
            }
        except Exception:
            return {
                'total_requests': 0,
                'open_requests': 0,
                'resolved_requests': 0,
                'recent_requests': 0,
                'high_priority_requests': 0,
                'resolution_rate': 0
            }