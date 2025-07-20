#!/usr/bin/env python3
"""
Cart Service - Business logic for shopping cart management
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from ..models.cart_models import CartItem, SavedCartItem
from ..models.product_models import Product
from ..core.orm.base_model import db_manager


class CartService:
    """Service for shopping cart operations"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or db_manager.get_session()
    
    def get_cart(self, customer_id: Optional[int] = None, session_id: Optional[str] = None) -> List[CartItem]:
        """Get cart items for customer or session"""
        if customer_id:
            return self.session.query(CartItem).filter(CartItem.customer_id == customer_id).all()
        elif session_id:
            return self.session.query(CartItem).filter(CartItem.session_id == session_id).all()
        return []
    
    def add_to_cart(self, product_id: int, quantity: int = 1, 
                   customer_id: Optional[int] = None, session_id: Optional[str] = None) -> Optional[CartItem]:
        """Add item to cart"""
        # Get product info
        product = self.session.query(Product).filter(Product.id == product_id).first()
        if not product:
            return None
        
        # Check if item already exists in cart
        existing_item = None
        if customer_id:
            existing_item = self.session.query(CartItem).filter(
                and_(CartItem.customer_id == customer_id, CartItem.product_id == product_id)
            ).first()
        elif session_id:
            existing_item = self.session.query(CartItem).filter(
                and_(CartItem.session_id == session_id, CartItem.product_id == product_id)
            ).first()
        
        if existing_item:
            # Update quantity
            existing_item.quantity += quantity
            existing_item.calculate_subtotal()
            self.session.commit()
            return existing_item
        else:
            # Create new cart item
            cart_item = CartItem(
                customer_id=customer_id,
                session_id=session_id,
                product_id=product_id,
                product_name=product.name,
                product_price=product.price,
                quantity=quantity
            )
            cart_item.calculate_subtotal()
            self.session.add(cart_item)
            self.session.commit()
            return cart_item
    
    def update_cart_item(self, item_id: int, quantity: int) -> Optional[CartItem]:
        """Update cart item quantity"""
        item = self.session.query(CartItem).filter(CartItem.id == item_id).first()
        if item:
            item.quantity = quantity
            item.calculate_subtotal()
            self.session.commit()
            return item
        return None
    
    def remove_from_cart(self, item_id: int) -> bool:
        """Remove item from cart"""
        item = self.session.query(CartItem).filter(CartItem.id == item_id).first()
        if item:
            self.session.delete(item)
            self.session.commit()
            return True
        return False
    
    def clear_cart(self, customer_id: Optional[int] = None, session_id: Optional[str] = None) -> bool:
        """Clear all items from cart"""
        if customer_id:
            self.session.query(CartItem).filter(CartItem.customer_id == customer_id).delete()
        elif session_id:
            self.session.query(CartItem).filter(CartItem.session_id == session_id).delete()
        else:
            return False
        
        self.session.commit()
        return True
    
    def get_cart_total(self, customer_id: Optional[int] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get cart totals"""
        items = self.get_cart(customer_id, session_id)
        
        subtotal = sum(item.subtotal for item in items)
        item_count = sum(item.quantity for item in items)
        
        return {
            'items': items,
            'subtotal': subtotal,
            'item_count': item_count
        }