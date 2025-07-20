#!/usr/bin/env python3
"""
Order Service - Business logic for order management
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models.order_models import Order, OrderItem, Payment
from ..models.customer_models import Customer
from ..core.orm.base_model import db_manager


class OrderService:
    """Service for order management operations"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or db_manager.get_session()
    
    def get_by_id(self, order_id: int) -> Optional[Order]:
        """Get order by ID"""
        return self.session.query(Order).filter(Order.id == order_id).first()
    
    def get_customer_orders(self, customer_id: int, page: int = 1, per_page: int = 20) -> Tuple[List[Order], int]:
        """Get orders for a specific customer"""
        query = self.session.query(Order).filter(Order.customer_id == customer_id)
        total = query.count()
        orders = query.order_by(Order.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        return orders, total
    
    def create_order(self, order_data: Dict[str, Any]) -> Order:
        """Create a new order"""
        order = Order(**order_data)
        self.session.add(order)
        self.session.commit()
        return order
    
    def update_order_status(self, order_id: int, status: str) -> Optional[Order]:
        """Update order status"""
        order = self.get_by_id(order_id)
        if order:
            order.status = status
            self.session.commit()
        return order
    
    def cancel_order(self, order_id: int) -> bool:
        """Cancel an order"""
        order = self.get_by_id(order_id)
        if order and order.status in ['pending', 'confirmed']:
            order.status = 'cancelled'
            self.session.commit()
            return True
        return False
    
    def add_order_item(self, order_id: int, item_data: Dict[str, Any]) -> Optional[OrderItem]:
        """Add an item to an order"""
        order = self.get_by_id(order_id)
        if order:
            item = OrderItem(order_id=order_id, **item_data)
            self.session.add(item)
            self.session.commit()
            return item
        return None