#!/usr/bin/env python3
"""
Customer Service - Business logic for customer management
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from ..models.customer_models import Customer, CustomerSession
from ..core.orm.base_model import db_manager


class CustomerService:
    """Service for customer management operations"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or db_manager.get_session()
    
    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        """Get customer by ID"""
        return self.session.query(Customer).filter(Customer.id == customer_id).first()
    
    def get_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email"""
        return self.session.query(Customer).filter(Customer.email == email).first()
    
    def create_customer(self, customer_data: Dict[str, Any]) -> Customer:
        """Create a new customer"""
        customer = Customer(**customer_data)
        self.session.add(customer)
        self.session.commit()
        return customer
    
    def update_customer(self, customer_id: int, update_data: Dict[str, Any]) -> Optional[Customer]:
        """Update customer information"""
        customer = self.get_by_id(customer_id)
        if customer:
            for key, value in update_data.items():
                if hasattr(customer, key):
                    setattr(customer, key, value)
            self.session.commit()
        return customer
    
    def delete_customer(self, customer_id: int) -> bool:
        """Soft delete a customer"""
        customer = self.get_by_id(customer_id)
        if customer:
            customer.soft_delete()
            self.session.commit()
            return True
        return False
    
    def authenticate_customer(self, email: str, password: str) -> Optional[Customer]:
        """Authenticate customer with email and password"""
        customer = self.get_by_email(email)
        if customer and customer.check_password(password):
            return customer
        return None