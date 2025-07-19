from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from ..orm.base_model import BaseModel


class Customer(BaseModel):
    """Customer model for the shop"""
    __tablename__ = 'customers'
    
    # Basic information
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    
    # Address information
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(50), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    
    # Preferences
    marketing_emails = Column(Boolean, default=True)
    newsletter = Column(Boolean, default=False)
    
    # Relationships
    llm_requests = relationship("LLMRequest", back_populates="customer")
    llm_conversations = relationship("LLMConversation", back_populates="customer")
    orders = relationship("Order", back_populates="customer")
    support_requests = relationship("SupportRequest", back_populates="customer")


class Order(BaseModel):
    """Order model for purchases"""
    __tablename__ = 'orders'
    
    # Customer link
    customer_id = Column(Integer, nullable=False, index=True)
    
    # Order details
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(20), default='pending', index=True)
    total_amount = Column(Integer, nullable=False)  # Amount in cents
    currency = Column(String(3), default='USD')
    
    # Payment information
    payment_processor = Column(String(20), nullable=True)  # 'stripe', 'paypal'
    transaction_id = Column(String(255), nullable=True, index=True)
    payment_status = Column(String(20), default='pending')
    
    # Relationships
    customer = relationship("Customer", back_populates="orders")


class SupportRequest(BaseModel):
    """Support request model"""
    __tablename__ = 'support_requests'
    
    # Customer link
    customer_id = Column(Integer, nullable=True, index=True)
    
    # Request details
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), default='open', index=True)
    priority = Column(String(10), default='normal', index=True)
    
    # Contact information (for non-registered users)
    contact_email = Column(String(255), nullable=True)
    contact_name = Column(String(100), nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="support_requests")