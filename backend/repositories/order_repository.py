#!/usr/bin/env python3
"""
Order Repository - Data access layer for order-related operations
Provides specialized queries and operations for orders, payments, and installation requests
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta

from core.repositories.base_repository import BaseRepository
from ..models.order_models import (
    Order, OrderItem, Payment, InstallationRequest,
    OrderStatus, PaymentStatus, PaymentProcessor
)


class OrderRepository(BaseRepository[Order]):
    """Repository for Order entities with specialized order operations"""
    
    def __init__(self, session: Session = None):
        super().__init__(Order, session)
    
    def get_by_order_number(self, order_number: str) -> Optional[Order]:
        """
        Get order by order number
        
        Args:
            order_number: Unique order number
            
        Returns:
            Order instance or None
        """
        return self.session.query(Order).filter(
            Order.order_number == order_number
        ).first()
    
    def get_customer_orders(self, customer_id: int, 
                           status: str = None,
                           limit: int = None,
                           offset: int = None) -> List[Order]:
        """
        Get orders for a specific customer
        
        Args:
            customer_id: Customer ID
            status: Optional status filter
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of customer orders
        """
        query = self.session.query(Order).options(
            joinedload(Order.order_items).joinedload(OrderItem.product)
        ).filter(
            Order.customer_id == customer_id
        )
        
        if status:
            query = query.filter(Order.status == status)
        
        query = query.order_by(desc(Order.created_at))
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_orders_by_status(self, status: str, 
                           limit: int = None,
                           offset: int = None) -> List[Order]:
        """
        Get orders by status
        
        Args:
            status: Order status
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of orders with specified status
        """
        query = self.session.query(Order).filter(
            Order.status == status
        ).order_by(desc(Order.created_at))
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_orders_by_date_range(self, start_date: datetime, 
                                end_date: datetime = None) -> List[Order]:
        """
        Get orders within date range
        
        Args:
            start_date: Start of date range
            end_date: End of date range (defaults to now)
            
        Returns:
            List of orders in date range
        """
        if end_date is None:
            end_date = datetime.utcnow()
        
        return self.session.query(Order).filter(
            and_(
                Order.created_at >= start_date,
                Order.created_at <= end_date
            )
        ).order_by(desc(Order.created_at)).all()
    
    def get_recent_orders(self, days: int = 30, limit: int = 50) -> List[Order]:
        """
        Get recent orders
        
        Args:
            days: Number of days back to look
            limit: Maximum number of orders
            
        Returns:
            List of recent orders
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        orders = self.get_orders_by_date_range(cutoff_date)
        return orders[:limit]
    
    def create_order(self, customer_id: int, billing_info: Dict[str, Any]) -> Order:
        """
        Create a new order
        
        Args:
            customer_id: Customer ID
            billing_info: Dictionary with billing information
            
        Returns:
            Created order instance
        """
        order = Order(
            customer_id=customer_id,
            billing_first_name=billing_info.get('first_name'),
            billing_last_name=billing_info.get('last_name'),
            billing_email=billing_info.get('email'),
            billing_phone=billing_info.get('phone'),
            billing_address_line1=billing_info.get('address_line1'),
            billing_address_line2=billing_info.get('address_line2'),
            billing_city=billing_info.get('city'),
            billing_state=billing_info.get('state'),
            billing_postal_code=billing_info.get('postal_code'),
            billing_country=billing_info.get('country'),
            terms_accepted=billing_info.get('terms_accepted', False),
            terms_accepted_at=datetime.utcnow() if billing_info.get('terms_accepted') else None,
            terms_ip_address=billing_info.get('ip_address'),
            customer_notes=billing_info.get('notes')
        )
        
        return self.create(order)
    
    def update_order_status(self, order_id: int, status: str) -> bool:
        """
        Update order status
        
        Args:
            order_id: Order ID
            status: New status
            
        Returns:
            True if successful
        """
        try:
            update_data = {Order.status: status}
            
            if status == OrderStatus.COMPLETED.value:
                update_data[Order.completed_at] = datetime.utcnow()
            elif status == OrderStatus.PROCESSING.value:
                update_data[Order.processed_at] = datetime.utcnow()
            
            self.session.query(Order).filter(
                Order.id == order_id
            ).update(update_data)
            return True
        except Exception:
            return False
    
    def get_pending_orders(self) -> List[Order]:
        """
        Get orders pending payment or processing
        
        Returns:
            List of pending orders
        """
        return self.session.query(Order).filter(
            Order.status.in_([OrderStatus.PENDING.value, OrderStatus.PAID.value])
        ).order_by(Order.created_at).all()
    
    def search_orders(self, search_term: str, limit: int = 50) -> List[Order]:
        """
        Search orders by order number, customer email, or customer name
        
        Args:
            search_term: Text to search for
            limit: Maximum number of results
            
        Returns:
            List of matching orders
        """
        if not search_term:
            return []
        
        search_conditions = or_(
            Order.order_number.ilike(f"%{search_term}%"),
            Order.billing_email.ilike(f"%{search_term}%"),
            Order.billing_first_name.ilike(f"%{search_term}%"),
            Order.billing_last_name.ilike(f"%{search_term}%")
        )
        
        return self.session.query(Order).filter(
            search_conditions
        ).order_by(desc(Order.created_at)).limit(limit).all()
    
    def get_order_stats(self) -> Dict[str, Any]:
        """
        Get order statistics
        
        Returns:
            Dictionary with order statistics
        """
        try:
            total_orders = self.session.query(func.count(Order.id)).scalar()
            
            completed_orders = self.session.query(func.count(Order.id)).filter(
                Order.status == OrderStatus.COMPLETED.value
            ).scalar()
            
            pending_orders = self.session.query(func.count(Order.id)).filter(
                Order.status.in_([OrderStatus.PENDING.value, OrderStatus.PAID.value])
            ).scalar()
            
            # Revenue calculation
            total_revenue = self.session.query(func.sum(Order.total_amount)).filter(
                Order.status.in_([OrderStatus.COMPLETED.value, OrderStatus.PAID.value])
            ).scalar()
            
            # Recent orders (last 30 days)
            recent_cutoff = datetime.utcnow() - timedelta(days=30)
            recent_orders = self.session.query(func.count(Order.id)).filter(
                Order.created_at >= recent_cutoff
            ).scalar()
            
            recent_revenue = self.session.query(func.sum(Order.total_amount)).filter(
                and_(
                    Order.created_at >= recent_cutoff,
                    Order.status.in_([OrderStatus.COMPLETED.value, OrderStatus.PAID.value])
                )
            ).scalar()
            
            # Average order value
            avg_order_value = self.session.query(func.avg(Order.total_amount)).filter(
                Order.status.in_([OrderStatus.COMPLETED.value, OrderStatus.PAID.value])
            ).scalar()
            
            return {
                'total_orders': total_orders or 0,
                'completed_orders': completed_orders or 0,
                'pending_orders': pending_orders or 0,
                'total_revenue': float(total_revenue or 0),
                'recent_orders': recent_orders or 0,
                'recent_revenue': float(recent_revenue or 0),
                'average_order_value': float(avg_order_value or 0),
                'completion_rate': (completed_orders / total_orders * 100) if total_orders > 0 else 0
            }
        except Exception:
            return {
                'total_orders': 0,
                'completed_orders': 0,
                'pending_orders': 0,
                'total_revenue': 0.0,
                'recent_orders': 0,
                'recent_revenue': 0.0,
                'average_order_value': 0.0,
                'completion_rate': 0
            }


class OrderItemRepository(BaseRepository[OrderItem]):
    """Repository for OrderItem entities"""
    
    def __init__(self, session: Session = None):
        super().__init__(OrderItem, session)
    
    def get_order_items(self, order_id: int) -> List[OrderItem]:
        """
        Get all items for an order
        
        Args:
            order_id: Order ID
            
        Returns:
            List of order items
        """
        return self.session.query(OrderItem).options(
            joinedload(OrderItem.product)
        ).filter(
            OrderItem.order_id == order_id
        ).all()
    
    def get_product_sales(self, product_id: int) -> List[OrderItem]:
        """
        Get all sales for a specific product
        
        Args:
            product_id: Product ID
            
        Returns:
            List of order items for the product
        """
        return self.session.query(OrderItem).options(
            joinedload(OrderItem.order)
        ).filter(
            OrderItem.product_id == product_id
        ).order_by(desc(OrderItem.created_at)).all()
    
    def generate_download_links(self, order_id: int, expires_hours: int = 48) -> bool:
        """
        Generate download links for all items in an order
        
        Args:
            order_id: Order ID
            expires_hours: Hours until download links expire
            
        Returns:
            True if successful
        """
        try:
            order_items = self.get_order_items(order_id)
            for item in order_items:
                if item.product and item.product.download_link:
                    item.generate_download_link(expires_hours)
            return True
        except Exception:
            return False
    
    def record_download(self, item_id: int) -> bool:
        """
        Record a download for an order item
        
        Args:
            item_id: Order item ID
            
        Returns:
            True if successful
        """
        try:
            item = self.get_by_id(item_id)
            if item and item.is_download_valid():
                item.record_download()
                
                # Also update product download count
                if item.product:
                    from .product_repository import ProductRepository
                    product_repo = ProductRepository(self.session)
                    product_repo.increment_download_count(item.product_id)
                
                return True
        except Exception:
            return False
        
        return False
    
    def get_downloadable_items(self, customer_id: int) -> List[OrderItem]:
        """
        Get all downloadable items for a customer
        
        Args:
            customer_id: Customer ID
            
        Returns:
            List of downloadable order items
        """
        return self.session.query(OrderItem).join(Order).filter(
            and_(
                Order.customer_id == customer_id,
                Order.status.in_([OrderStatus.COMPLETED.value, OrderStatus.PAID.value]),
                OrderItem.download_link.isnot(None),
                OrderItem.download_expires_at > datetime.utcnow()
            )
        ).order_by(desc(OrderItem.created_at)).all()


class PaymentRepository(BaseRepository[Payment]):
    """Repository for Payment entities"""
    
    def __init__(self, session: Session = None):
        super().__init__(Payment, session)
    
    def create_payment(self, order_id: int, amount: float, 
                      payment_processor: str, transaction_id: str = None) -> Payment:
        """
        Create a new payment record
        
        Args:
            order_id: Order ID
            amount: Payment amount
            payment_processor: Payment processor used
            transaction_id: Transaction ID from payment processor
            
        Returns:
            Created payment instance
        """
        payment = Payment(
            order_id=order_id,
            amount=amount,
            payment_processor=payment_processor,
            transaction_id=transaction_id
        )
        
        return self.create(payment)
    
    def get_order_payments(self, order_id: int) -> List[Payment]:
        """
        Get all payments for an order
        
        Args:
            order_id: Order ID
            
        Returns:
            List of payments for the order
        """
        return self.session.query(Payment).filter(
            Payment.order_id == order_id
        ).order_by(Payment.created_at).all()
    
    def get_successful_payments(self, start_date: datetime = None, 
                               end_date: datetime = None) -> List[Payment]:
        """
        Get all successful payments in date range
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of successful payments
        """
        query = self.session.query(Payment).filter(
            Payment.status == PaymentStatus.SUCCESS.value
        )
        
        if start_date:
            query = query.filter(Payment.completed_at >= start_date)
        if end_date:
            query = query.filter(Payment.completed_at <= end_date)
        
        return query.order_by(desc(Payment.completed_at)).all()
    
    def get_failed_payments(self, limit: int = 50) -> List[Payment]:
        """
        Get recent failed payments for investigation
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of failed payments
        """
        return self.session.query(Payment).filter(
            Payment.status == PaymentStatus.FAILED.value
        ).order_by(desc(Payment.failed_at)).limit(limit).all()
    
    def update_payment_status(self, payment_id: int, status: str, 
                             transaction_id: str = None, 
                             error_code: str = None,
                             error_message: str = None) -> bool:
        """
        Update payment status
        
        Args:
            payment_id: Payment ID
            status: New payment status
            transaction_id: Transaction ID from processor
            error_code: Error code if failed
            error_message: Error message if failed
            
        Returns:
            True if successful
        """
        try:
            payment = self.get_by_id(payment_id)
            if payment:
                if status == PaymentStatus.SUCCESS.value:
                    payment.mark_successful(transaction_id)
                elif status == PaymentStatus.FAILED.value:
                    payment.mark_failed(error_code, error_message)
                else:
                    payment.status = status
                
                return True
        except Exception:
            return False
        
        return False
    
    def get_payment_stats(self) -> Dict[str, Any]:
        """
        Get payment statistics
        
        Returns:
            Dictionary with payment statistics
        """
        try:
            total_payments = self.session.query(func.count(Payment.id)).scalar()
            
            successful_payments = self.session.query(func.count(Payment.id)).filter(
                Payment.status == PaymentStatus.SUCCESS.value
            ).scalar()
            
            failed_payments = self.session.query(func.count(Payment.id)).filter(
                Payment.status == PaymentStatus.FAILED.value
            ).scalar()
            
            total_revenue = self.session.query(func.sum(Payment.amount)).filter(
                Payment.status == PaymentStatus.SUCCESS.value
            ).scalar()
            
            # Payment processor breakdown
            stripe_payments = self.session.query(func.count(Payment.id)).filter(
                and_(
                    Payment.payment_processor == PaymentProcessor.STRIPE.value,
                    Payment.status == PaymentStatus.SUCCESS.value
                )
            ).scalar()
            
            paypal_payments = self.session.query(func.count(Payment.id)).filter(
                and_(
                    Payment.payment_processor == PaymentProcessor.PAYPAL.value,
                    Payment.status == PaymentStatus.SUCCESS.value
                )
            ).scalar()
            
            return {
                'total_payments': total_payments or 0,
                'successful_payments': successful_payments or 0,
                'failed_payments': failed_payments or 0,
                'total_revenue': float(total_revenue or 0),
                'success_rate': (successful_payments / total_payments * 100) if total_payments > 0 else 0,
                'stripe_payments': stripe_payments or 0,
                'paypal_payments': paypal_payments or 0
            }
        except Exception:
            return {
                'total_payments': 0,
                'successful_payments': 0,
                'failed_payments': 0,
                'total_revenue': 0.0,
                'success_rate': 0,
                'stripe_payments': 0,
                'paypal_payments': 0
            }


class InstallationRequestRepository(BaseRepository[InstallationRequest]):
    """Repository for InstallationRequest entities"""
    
    def __init__(self, session: Session = None):
        super().__init__(InstallationRequest, session)
    
    def create_installation_request(self, order_id: int, 
                                   odoo_version: str,
                                   installation_period: datetime,
                                   tech_contact_name: str,
                                   tech_contact_email: str,
                                   comments: str = None,
                                   tech_contact_phone: str = None) -> InstallationRequest:
        """
        Create a new installation request
        
        Args:
            order_id: Order ID
            odoo_version: Odoo version requested
            installation_period: Requested installation date
            tech_contact_name: Technical contact name
            tech_contact_email: Technical contact email
            comments: Additional comments
            tech_contact_phone: Technical contact phone
            
        Returns:
            Created installation request instance
        """
        request = InstallationRequest(
            order_id=order_id,
            odoo_version=odoo_version,
            installation_period=installation_period,
            tech_contact_name=tech_contact_name,
            tech_contact_email=tech_contact_email,
            comments=comments,
            tech_contact_phone=tech_contact_phone
        )
        
        return self.create(request)
    
    def get_pending_requests(self) -> List[InstallationRequest]:
        """
        Get all pending installation requests
        
        Returns:
            List of pending installation requests
        """
        return self.session.query(InstallationRequest).filter(
            InstallationRequest.status == 'pending'
        ).order_by(InstallationRequest.installation_period).all()
    
    def get_order_installation_requests(self, order_id: int) -> List[InstallationRequest]:
        """
        Get installation requests for an order
        
        Args:
            order_id: Order ID
            
        Returns:
            List of installation requests for the order
        """
        return self.session.query(InstallationRequest).filter(
            InstallationRequest.order_id == order_id
        ).order_by(InstallationRequest.created_at).all()
    
    def update_request_status(self, request_id: int, status: str, 
                             quote_amount: float = None) -> bool:
        """
        Update installation request status
        
        Args:
            request_id: Installation request ID
            status: New status
            quote_amount: Quote amount if providing quote
            
        Returns:
            True if successful
        """
        try:
            request = self.get_by_id(request_id)
            if request:
                request.status = status
                if quote_amount and status == 'quoted':
                    request.send_quote(quote_amount)
                return True
        except Exception:
            return False
        
        return False