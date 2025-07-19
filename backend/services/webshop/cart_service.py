#!/usr/bin/env python3
"""
Cart Service - Business logic for shopping cart management
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from .base_service import BaseService, ValidationError, ServiceError
from ..repositories.cart_repository import CartRepository
from ..models.cart_models import CartItem
from ..models.webshop_models import Product

logger = logging.getLogger(__name__)


class CartService(BaseService[CartItem]):
    """Service for shopping cart operations"""
    
    def __init__(self, repository: CartRepository = None, session: Session = None):
        super().__init__(repository, session)
    
    def _create_repository(self) -> CartRepository:
        """Create CartRepository instance"""
        return CartRepository(self._session)
    
    def _create_entity_from_data(self, entity_data: Dict[str, Any]) -> CartItem:
        """Create CartItem instance from data dictionary"""
        return CartItem(**entity_data)
    
    def _validate_business_rules(self, cart_item: CartItem, 
                                is_create: bool = True) -> Dict[str, List[str]]:
        """Validate cart item business rules"""
        errors = {}
        
        # Validate quantity
        if cart_item.quantity is None or cart_item.quantity <= 0:
            errors['quantity'] = ['Quantity must be greater than 0']
        
        # Validate product exists
        if cart_item.product_id:
            from ..repositories.product_repository import ProductRepository
            product_repo = ProductRepository(self.session)
            product = product_repo.get_by_id(cart_item.product_id)
            if not product:
                errors['product_id'] = ['Product not found']
            elif not product.is_active:
                errors['product_id'] = ['Product is not available']
        
        return errors
    
    def _before_create(self, cart_item: CartItem, entity_data: Dict[str, Any]):
        """Set defaults before creating cart item"""
        if not cart_item.session_id and not cart_item.customer_id:
            raise ValidationError("Either session_id or customer_id is required")
        
        # Get product details
        if cart_item.product_id:
            from ..repositories.product_repository import ProductRepository
            product_repo = ProductRepository(self.session)
            product = product_repo.get_by_id(cart_item.product_id)
            
            if product:
                cart_item.product_name = product.name
                cart_item.product_price = product.price
                cart_item.subtotal = cart_item.product_price * cart_item.quantity
    
    def _before_update(self, cart_item: CartItem, entity_data: Dict[str, Any]):
        """Update subtotal before updating cart item"""
        if 'quantity' in entity_data and cart_item.product_price:
            cart_item.subtotal = cart_item.product_price * cart_item.quantity
    
    def get_cart_items(self, customer_id: int = None, session_id: str = None) -> List[CartItem]:
        """Get all cart items for user"""
        try:
            if customer_id:
                return self.repository.get_by_customer_id(customer_id)
            elif session_id:
                return self.repository.get_by_session_id(session_id)
            else:
                return []
        except Exception as e:
            logger.error(f"Error getting cart items: {e}")
            return []
    
    def add_to_cart(self, product_id: int, quantity: int, 
                   customer_id: int = None, session_id: str = None) -> Optional[CartItem]:
        """Add item to cart or update existing item quantity"""
        try:
            if not customer_id and not session_id:
                raise ValidationError("Either customer_id or session_id is required")
            
            # Check if item already exists in cart
            existing_item = None
            if customer_id:
                existing_item = self.repository.get_by_customer_and_product(customer_id, product_id)
            elif session_id:
                existing_item = self.repository.get_by_session_and_product(session_id, product_id)
            
            if existing_item:
                # Update existing item quantity
                new_quantity = existing_item.quantity + quantity
                return self.update_cart_item(existing_item.id, new_quantity, customer_id, session_id)
            else:
                # Create new cart item
                cart_data = {
                    'product_id': product_id,
                    'quantity': quantity,
                    'customer_id': customer_id,
                    'session_id': session_id
                }
                return self.create(cart_data)
                
        except Exception as e:
            logger.error(f"Error adding to cart: {e}")
            return None
    
    def update_cart_item(self, item_id: int, quantity: int,
                        customer_id: int = None, session_id: str = None) -> Optional[CartItem]:
        """Update cart item quantity"""
        try:
            # Get cart item
            cart_item = self.get_by_id(item_id)
            if not cart_item:
                return None
            
            # Verify ownership
            if customer_id and cart_item.customer_id != customer_id:
                return None
            if session_id and cart_item.session_id != session_id:
                return None
            
            if quantity <= 0:
                # Remove item if quantity is 0 or negative
                self.remove_from_cart(item_id, customer_id, session_id)
                return None
            else:
                # Update quantity
                return self.update(item_id, {'quantity': quantity})
                
        except Exception as e:
            logger.error(f"Error updating cart item: {e}")
            return None
    
    def remove_from_cart(self, item_id: int, 
                        customer_id: int = None, session_id: str = None) -> bool:
        """Remove item from cart"""
        try:
            # Get cart item
            cart_item = self.get_by_id(item_id)
            if not cart_item:
                return False
            
            # Verify ownership
            if customer_id and cart_item.customer_id != customer_id:
                return False
            if session_id and cart_item.session_id != session_id:
                return False
            
            # Delete cart item
            return self.delete(item_id)
            
        except Exception as e:
            logger.error(f"Error removing from cart: {e}")
            return False
    
    def clear_cart(self, customer_id: int = None, session_id: str = None) -> bool:
        """Clear all items from cart"""
        try:
            if customer_id:
                return self.repository.clear_by_customer_id(customer_id)
            elif session_id:
                return self.repository.clear_by_session_id(session_id)
            else:
                return False
        except Exception as e:
            logger.error(f"Error clearing cart: {e}")
            return False
    
    def get_cart_item_count(self, customer_id: int = None, session_id: str = None) -> int:
        """Get total number of items in cart"""
        try:
            cart_items = self.get_cart_items(customer_id, session_id)
            return sum(item.quantity for item in cart_items)
        except Exception as e:
            logger.error(f"Error getting cart count: {e}")
            return 0
    
    def get_cart_subtotal(self, customer_id: int = None, session_id: str = None) -> float:
        """Get cart subtotal"""
        try:
            cart_items = self.get_cart_items(customer_id, session_id)
            return sum(item.subtotal for item in cart_items)
        except Exception as e:
            logger.error(f"Error calculating cart subtotal: {e}")
            return 0.0
    
    def merge_guest_cart_to_customer(self, session_id: str, customer_id: int) -> bool:
        """Merge guest cart items to customer cart after login"""
        try:
            # Get guest cart items
            guest_items = self.repository.get_by_session_id(session_id)
            
            for guest_item in guest_items:
                # Check if customer already has this product
                existing_item = self.repository.get_by_customer_and_product(
                    customer_id, guest_item.product_id
                )
                
                if existing_item:
                    # Update quantity
                    new_quantity = existing_item.quantity + guest_item.quantity
                    self.update(existing_item.id, {'quantity': new_quantity})
                else:
                    # Create new item for customer
                    cart_data = {
                        'product_id': guest_item.product_id,
                        'product_name': guest_item.product_name,
                        'product_price': guest_item.product_price,
                        'quantity': guest_item.quantity,
                        'subtotal': guest_item.subtotal,
                        'customer_id': customer_id,
                        'session_id': None
                    }
                    self.create(cart_data)
            
            # Clear guest cart
            self.repository.clear_by_session_id(session_id)
            
            logger.info(f"Merged {len(guest_items)} items from guest cart to customer {customer_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error merging guest cart: {e}")
            return False
    
    def cleanup_old_guest_carts(self, days_old: int = 7) -> bool:
        """Clean up old guest cart items"""
        try:
            return self.repository.cleanup_old_guest_carts(days_old)
        except Exception as e:
            logger.error(f"Error cleaning up old guest carts: {e}")
            return False
    
    def validate_cart_for_checkout(self, customer_id: int = None, session_id: str = None) -> Dict[str, Any]:
        """Validate cart items for checkout"""
        try:
            cart_items = self.get_cart_items(customer_id, session_id)
            
            if not cart_items:
                return {'valid': False, 'errors': ['Cart is empty']}
            
            errors = []
            updated_items = []
            
            # Check each item
            for item in cart_items:
                from ..repositories.product_repository import ProductRepository
                product_repo = ProductRepository(self.session)
                product = product_repo.get_by_id(item.product_id)
                
                if not product:
                    errors.append(f"Product '{item.product_name}' is no longer available")
                elif not product.is_active:
                    errors.append(f"Product '{item.product_name}' is currently unavailable")
                elif product.price != item.product_price:
                    # Price changed - update cart item
                    self.update(item.id, {
                        'product_price': product.price,
                        'subtotal': product.price * item.quantity
                    })
                    updated_items.append({
                        'name': item.product_name,
                        'old_price': float(item.product_price),
                        'new_price': float(product.price)
                    })
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'updated_items': updated_items
            }
            
        except Exception as e:
            logger.error(f"Error validating cart: {e}")
            return {'valid': False, 'errors': ['Error validating cart']}