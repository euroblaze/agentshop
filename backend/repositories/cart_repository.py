#!/usr/bin/env python3
"""
Cart Repository - Data access layer for shopping cart operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
import logging

try:
    from ..orm.base_repository import BaseRepository
    from ..models.cart_models import CartItem, SavedCartItem
except ImportError:
    from orm.base_repository import BaseRepository
    from models.cart_models import CartItem, SavedCartItem

logger = logging.getLogger(__name__)


class CartRepository(BaseRepository[CartItem]):
    """Repository for cart item operations"""
    
    def __init__(self, session: Session):
        super().__init__(CartItem, session)
    
    def get_by_customer_id(self, customer_id: int) -> List[CartItem]:
        """Get all cart items for a customer"""
        try:
            return self.session.query(CartItem).filter(
                CartItem.customer_id == customer_id
            ).order_by(CartItem.created_at.desc()).all()
        except Exception as e:
            logger.error(f"Error getting cart items by customer ID: {e}")
            return []
    
    def get_by_session_id(self, session_id: str) -> List[CartItem]:
        """Get all cart items for a session"""
        try:
            return self.session.query(CartItem).filter(
                CartItem.session_id == session_id
            ).order_by(CartItem.created_at.desc()).all()
        except Exception as e:
            logger.error(f"Error getting cart items by session ID: {e}")
            return []
    
    def get_by_customer_and_product(self, customer_id: int, product_id: int) -> Optional[CartItem]:
        """Get cart item by customer and product"""
        try:
            return self.session.query(CartItem).filter(
                and_(
                    CartItem.customer_id == customer_id,
                    CartItem.product_id == product_id
                )
            ).first()
        except Exception as e:
            logger.error(f"Error getting cart item by customer and product: {e}")
            return None
    
    def get_by_session_and_product(self, session_id: str, product_id: int) -> Optional[CartItem]:
        """Get cart item by session and product"""
        try:
            return self.session.query(CartItem).filter(
                and_(
                    CartItem.session_id == session_id,
                    CartItem.product_id == product_id
                )
            ).first()
        except Exception as e:
            logger.error(f"Error getting cart item by session and product: {e}")
            return None
    
    def clear_by_customer_id(self, customer_id: int) -> bool:
        """Clear all cart items for a customer"""
        try:
            deleted_count = self.session.query(CartItem).filter(
                CartItem.customer_id == customer_id
            ).delete(synchronize_session=False)
            
            self.session.commit()
            logger.info(f"Cleared {deleted_count} cart items for customer {customer_id}")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error clearing cart for customer {customer_id}: {e}")
            return False
    
    def clear_by_session_id(self, session_id: str) -> bool:
        """Clear all cart items for a session"""
        try:
            deleted_count = self.session.query(CartItem).filter(
                CartItem.session_id == session_id
            ).delete(synchronize_session=False)
            
            self.session.commit()
            logger.info(f"Cleared {deleted_count} cart items for session {session_id}")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error clearing cart for session {session_id}: {e}")
            return False
    
    def get_cart_count(self, customer_id: int = None, session_id: str = None) -> int:
        """Get total quantity of items in cart"""
        try:
            query = self.session.query(CartItem.quantity)
            
            if customer_id:
                query = query.filter(CartItem.customer_id == customer_id)
            elif session_id:
                query = query.filter(CartItem.session_id == session_id)
            else:
                return 0
            
            result = query.all()
            return sum(item.quantity for item in result)
            
        except Exception as e:
            logger.error(f"Error getting cart count: {e}")
            return 0
    
    def cleanup_old_guest_carts(self, days_old: int = 7) -> bool:
        """Clean up old guest cart items"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            deleted_count = self.session.query(CartItem).filter(
                and_(
                    CartItem.customer_id.is_(None),
                    CartItem.session_id.isnot(None),
                    CartItem.created_at < cutoff_date
                )
            ).delete(synchronize_session=False)
            
            self.session.commit()
            logger.info(f"Cleaned up {deleted_count} old guest cart items")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error cleaning up old guest carts: {e}")
            return False
    
    def get_items_by_product_id(self, product_id: int) -> List[CartItem]:
        """Get all cart items containing a specific product"""
        try:
            return self.session.query(CartItem).filter(
                CartItem.product_id == product_id
            ).all()
        except Exception as e:
            logger.error(f"Error getting cart items by product ID: {e}")
            return []
    
    def update_product_info_in_carts(self, product_id: int, name: str, price: float) -> bool:
        """Update product information in all cart items when product changes"""
        try:
            updated_count = self.session.query(CartItem).filter(
                CartItem.product_id == product_id
            ).update({
                'product_name': name,
                'product_price': price,
                'subtotal': CartItem.quantity * price,
                'updated_at': datetime.utcnow()
            }, synchronize_session=False)
            
            self.session.commit()
            logger.info(f"Updated product info in {updated_count} cart items")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating product info in carts: {e}")
            return False


class SavedCartRepository(BaseRepository[SavedCartItem]):
    """Repository for saved cart items (wishlist)"""
    
    def __init__(self, session: Session):
        super().__init__(SavedCartItem, session)
    
    def get_by_customer_id(self, customer_id: int) -> List[SavedCartItem]:
        """Get all saved items for a customer"""
        try:
            return self.session.query(SavedCartItem).filter(
                SavedCartItem.customer_id == customer_id
            ).order_by(SavedCartItem.created_at.desc()).all()
        except Exception as e:
            logger.error(f"Error getting saved items by customer ID: {e}")
            return []
    
    def get_by_customer_and_product(self, customer_id: int, product_id: int) -> Optional[SavedCartItem]:
        """Get saved item by customer and product"""
        try:
            return self.session.query(SavedCartItem).filter(
                and_(
                    SavedCartItem.customer_id == customer_id,
                    SavedCartItem.product_id == product_id
                )
            ).first()
        except Exception as e:
            logger.error(f"Error getting saved item by customer and product: {e}")
            return None
    
    def clear_by_customer_id(self, customer_id: int) -> bool:
        """Clear all saved items for a customer"""
        try:
            deleted_count = self.session.query(SavedCartItem).filter(
                SavedCartItem.customer_id == customer_id
            ).delete(synchronize_session=False)
            
            self.session.commit()
            logger.info(f"Cleared {deleted_count} saved items for customer {customer_id}")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error clearing saved items for customer {customer_id}: {e}")
            return False