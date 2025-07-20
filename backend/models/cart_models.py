#!/usr/bin/env python3
"""
Cart Models - Database models for shopping cart functionality
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

try:
    from ..core.orm.base_model import BaseModel
    from .customer_models import Customer
    from .product_models import Product
except ImportError:
    from core.orm.base_model import BaseModel
    from models.customer_models import Customer
    from models.product_models import Product


class CartItem(BaseModel):
    """Shopping cart item model"""
    
    __tablename__ = 'cart_items'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # User identification (either customer or session)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    
    # Product information
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    product_name = Column(String(255), nullable=False)  # Denormalized for performance
    product_price = Column(Float, nullable=False)  # Price at time of adding to cart
    
    # Cart item details
    quantity = Column(Integer, nullable=False, default=1)
    subtotal = Column(Float, nullable=False, default=0.0)
    
    # Metadata
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    customer = relationship("Customer", back_populates="cart_items")
    product = relationship("Product")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.subtotal == 0.0 and self.product_price and self.quantity:
            self.subtotal = self.product_price * self.quantity
    
    def calculate_subtotal(self):
        """Calculate and update subtotal"""
        if self.product_price and self.quantity:
            self.subtotal = self.product_price * self.quantity
            return self.subtotal
        return 0.0
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'session_id': self.session_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'product_price': self.product_price,
            'quantity': self.quantity,
            'subtotal': self.subtotal,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<CartItem(id={self.id}, product='{self.product_name}', quantity={self.quantity}, subtotal={self.subtotal})>"


class SavedCartItem(BaseModel):
    """Saved cart item (wishlist/save for later)"""
    
    __tablename__ = 'saved_cart_items'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # User identification
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False, index=True)
    
    # Product information
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    product_name = Column(String(255), nullable=False)
    product_price = Column(Float, nullable=False)  # Price when saved
    
    # Save details
    quantity = Column(Integer, nullable=False, default=1)
    notes = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    customer = relationship("Customer", back_populates="saved_items")
    product = relationship("Product")
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'product_price': self.product_price,
            'quantity': self.quantity,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<SavedCartItem(id={self.id}, product='{self.product_name}', quantity={self.quantity})>"


# Add relationships to existing models (update imports as needed)
try:
    # Add cart relationships to Customer model
    Customer.cart_items = relationship("CartItem", back_populates="customer", cascade="all, delete-orphan")
    Customer.saved_items = relationship("SavedCartItem", back_populates="customer", cascade="all, delete-orphan")
except:
    # Handle case where Customer model doesn't exist yet
    pass