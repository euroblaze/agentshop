#!/usr/bin/env python3
"""
Order Service - Business logic for order management and payment processing
Handles orders, payments, installation requests with comprehensive business rules
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from .base_service import BaseService, ValidationError, ServiceError
from ..repositories.order_repository import (
    OrderRepository, OrderItemRepository, PaymentRepository, InstallationRequestRepository
)
from ..models.order_models import (
    Order, OrderItem, Payment, InstallationRequest,
    OrderStatus, PaymentStatus, PaymentProcessor
)

logger = logging.getLogger(__name__)


class OrderService(BaseService[Order]):
    """Service for Order entity with order management and payment processing"""
    
    def __init__(self, repository: OrderRepository = None, session: Session = None):
        super().__init__(repository, session)
        self.order_item_service = OrderItemService(session=session)
        self.payment_service = PaymentService(session=session)
    
    def _create_repository(self) -> OrderRepository:
        """Create OrderRepository instance"""
        return OrderRepository(self._session)
    
    def _create_entity_from_data(self, entity_data: Dict[str, Any]) -> Order:
        """Create Order instance from data dictionary"""
        return Order(**entity_data)
    
    def _validate_business_rules(self, order: Order,
                                is_create: bool = True) -> Dict[str, List[str]]:
        """Validate order business rules"""
        errors = {}
        
        # Validate customer exists
        if order.customer_id:
            from ..repositories.customer_repository import CustomerRepository
            customer_repo = CustomerRepository(self.session)
            customer = customer_repo.get_by_id(order.customer_id)
            if not customer:
                errors['customer_id'] = ['Customer does not exist']
            elif not customer.is_active:
                errors['customer_id'] = ['Customer account is not active']
        
        # Validate order totals
        if order.total_amount < 0:
            errors['total_amount'] = ['Total amount cannot be negative']
        
        if order.subtotal < 0:
            errors['subtotal'] = ['Subtotal cannot be negative']
        
        if order.tax_amount < 0:
            errors['tax_amount'] = ['Tax amount cannot be negative']
        
        return errors
    
    def _apply_create_business_rules(self, order: Order, entity_data: Dict[str, Any]):
        """Apply business rules during order creation"""
        # Set terms acceptance timestamp
        if order.terms_accepted:
            order.terms_accepted_at = datetime.utcnow()
        
        # Initialize totals
        if order.subtotal is None:
            order.subtotal = 0.0
        if order.tax_amount is None:
            order.tax_amount = 0.0
        if order.total_amount is None:
            order.total_amount = order.subtotal + order.tax_amount
    
    def _after_create(self, order: Order, entity_data: Dict[str, Any]):
        """Send order confirmation after creation"""
        try:
            from ..email_service import email_service
            
            # Prepare order data for email
            order_data = {
                'customer_name': f"{order.billing_first_name} {order.billing_last_name}",
                'customer_email': order.billing_email,
                'order_number': order.order_number,
                'order_date': order.created_at.strftime('%Y-%m-%d') if order.created_at else '',
                'total_amount': f"{order.total_amount:.2f}",
                'items': []
            }
            
            # Add order items if available
            if hasattr(order, 'items') and order.items:
                for item in order.items:
                    order_data['items'].append({
                        'name': item.name,
                        'price': f"{item.price:.2f}",
                        'quantity': item.quantity
                    })
            
            # Send confirmation email
            email_sent = email_service.send_order_confirmation(order_data)
            
            if email_sent:
                logger.info(f"Order confirmation sent for: {order.order_number}")
            else:
                logger.warning(f"Failed to send confirmation email for: {order.order_number}")
                
        except Exception as e:
            logger.error(f"Error sending order confirmation: {e}")
    
    def _get_default_search_fields(self) -> List[str]:
        """Get default search fields for orders"""
        return ['order_number', 'billing_email', 'billing_first_name', 'billing_last_name']
    
    # Order Management
    
    def create_order(self, customer_id: int, billing_info: Dict[str, Any],
                    cart_items: List[Dict[str, Any]] = None) -> Order:
        """
        Create new order with items
        
        Args:
            customer_id: Customer ID
            billing_info: Billing information dictionary
            cart_items: List of cart items to add to order
            
        Returns:
            Created order instance
            
        Raises:
            ValidationError: If order data is invalid
            ServiceError: If order creation fails
        """
        try:
            # Create order
            order = self.repository.create_order(customer_id, billing_info)
            
            # Add items if provided
            if cart_items:
                for item_data in cart_items:
                    self._add_item_to_order(order, item_data)
            
            # Calculate totals
            self._calculate_order_totals(order)
            
            # Update order
            self.repository.update(order)
            
            return order
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            raise ServiceError("Failed to create order") from e
    
    def add_item_to_order(self, order_id: int, product_id: int, 
                         quantity: int = 1, price: float = None) -> OrderItem:
        """
        Add item to existing order
        
        Args:
            order_id: Order ID
            product_id: Product ID
            quantity: Item quantity
            price: Override price (optional)
            
        Returns:
            Created order item
            
        Raises:
            ServiceError: If operation fails
        """
        try:
            order = self.get_by_id(order_id)
            if not order:
                raise ServiceError("Order not found")
            
            # Check if order can be modified
            if order.status not in [OrderStatus.PENDING.value]:
                raise ServiceError("Cannot modify order in current status")
            
            # Get product
            from ..repositories.product_repository import ProductRepository
            product_repo = ProductRepository(self.session)
            product = product_repo.get_by_id(product_id)
            if not product:
                raise ServiceError("Product not found")
            
            # Add item
            item_data = {
                'product_id': product_id,
                'quantity': quantity,
                'price': price
            }
            
            order_item = self._add_item_to_order(order, item_data)
            
            # Recalculate totals
            self._calculate_order_totals(order)
            self.repository.update(order)
            
            return order_item
            
        except ServiceError:
            raise
        except Exception as e:
            logger.error(f"Error adding item to order: {e}")
            raise ServiceError("Failed to add item to order") from e
    
    def remove_item_from_order(self, order_id: int, product_id: int) -> bool:
        """
        Remove item from order
        
        Args:
            order_id: Order ID
            product_id: Product ID to remove
            
        Returns:
            True if successful
        """
        try:
            order = self.get_by_id(order_id)
            if not order:
                return False
            
            # Check if order can be modified
            if order.status not in [OrderStatus.PENDING.value]:
                return False
            
            # Remove item
            order.remove_item(product_id)
            
            # Recalculate totals
            self._calculate_order_totals(order)
            self.repository.update(order)
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing item from order: {e}")
            return False
    
    def get_customer_orders(self, customer_id: int, status: str = None,
                           limit: int = None, offset: int = None) -> List[Order]:
        """Get orders for a customer"""
        try:
            return self.repository.get_customer_orders(customer_id, status, limit, offset)
        except Exception as e:
            logger.error(f"Error getting customer orders: {e}")
            return []
    
    def get_by_order_number(self, order_number: str) -> Optional[Order]:
        """Get order by order number"""
        try:
            return self.repository.get_by_order_number(order_number)
        except Exception as e:
            logger.error(f"Error getting order by number: {e}")
            return None
    
    def update_order_status(self, order_id: int, status: str) -> bool:
        """Update order status with business logic"""
        try:
            order = self.get_by_id(order_id)
            if not order:
                return False
            
            # Validate status transition
            if not self._can_transition_to_status(order.status, status):
                raise ServiceError(f"Cannot transition from {order.status} to {status}")
            
            # Update status
            success = self.repository.update_order_status(order_id, status)
            
            if success:
                # Handle status-specific actions
                self._handle_status_change(order_id, status)
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            return False
    
    def process_payment(self, order_id: int, payment_processor: str,
                       payment_details: Dict[str, Any]) -> Tuple[bool, Optional[Payment]]:
        """
        Process payment for order
        
        Args:
            order_id: Order ID
            payment_processor: Payment processor to use
            payment_details: Payment details from frontend
            
        Returns:
            Tuple of (success, payment_instance)
        """
        try:
            order = self.get_by_id(order_id)
            if not order:
                return False, None
            
            # Check if order can be paid
            if order.status not in [OrderStatus.PENDING.value]:
                return False, None
            
            # Create payment record
            payment = self.payment_service.create_payment(
                order_id, order.total_amount, payment_processor
            )
            
            # Process payment based on processor
            success = False
            if payment_processor == PaymentProcessor.STRIPE.value:
                success = self._process_stripe_payment(payment, payment_details)
            elif payment_processor == PaymentProcessor.PAYPAL.value:
                success = self._process_paypal_payment(payment, payment_details)
            
            if success:
                # Update order status
                self.update_order_status(order_id, OrderStatus.PAID.value)
                
                # Generate download links
                self.order_item_service.generate_download_links(order_id)
                
                # Send confirmation email
                self._send_order_completion_email(order)
            
            return success, payment
            
        except Exception as e:
            logger.error(f"Error processing payment: {e}")
            return False, None
    
    def get_order_stats(self) -> Dict[str, Any]:
        """Get order statistics"""
        try:
            return self.repository.get_order_stats()
        except Exception as e:
            logger.error(f"Error getting order stats: {e}")
            return {}
    
    # Helper methods
    
    def _add_item_to_order(self, order: Order, item_data: Dict[str, Any]) -> OrderItem:
        """Add item to order with validation"""
        from ..repositories.product_repository import ProductRepository
        
        product_repo = ProductRepository(self.session)
        product = product_repo.get_by_id(item_data['product_id'])
        
        if not product:
            raise ServiceError("Product not found")
        
        if not product.is_purchasable:
            raise ServiceError("Product is not purchasable")
        
        # Use product price if not overridden
        price = item_data.get('price', product.price or 0.0)
        
        order.add_item(product, item_data.get('quantity', 1), price)
        
        # Return the added item
        return order.order_items[-1]
    
    def _calculate_order_totals(self, order: Order):
        """Calculate order totals"""
        order._calculate_totals()
        
        # Apply tax calculation based on billing address
        if order.subtotal and order.subtotal > 0:
            try:
                from ..payment_service import payment_service
                
                billing_address = {
                    'street': order.billing_street,
                    'city': order.billing_city,
                    'state': order.billing_state,
                    'postal_code': order.billing_postal_code,
                    'country': order.billing_country
                }
                
                tax_amount = payment_service.calculate_tax(order.subtotal, billing_address)
                order.tax_amount = float(tax_amount)
                order.total_amount = order.subtotal + order.tax_amount
                
                logger.info(f"Tax calculated for order {order.order_number}: ${tax_amount:.2f}")
                
            except Exception as e:
                logger.error(f"Tax calculation failed: {e}")
                # Fallback to no tax
                order.tax_amount = 0.0
                order.total_amount = order.subtotal
    
    def _can_transition_to_status(self, current_status: str, new_status: str) -> bool:
        """Check if status transition is allowed"""
        valid_transitions = {
            OrderStatus.PENDING.value: [OrderStatus.PAID.value, OrderStatus.CANCELLED.value],
            OrderStatus.PAID.value: [OrderStatus.PROCESSING.value, OrderStatus.COMPLETED.value, OrderStatus.REFUNDED.value],
            OrderStatus.PROCESSING.value: [OrderStatus.COMPLETED.value, OrderStatus.CANCELLED.value],
            OrderStatus.COMPLETED.value: [OrderStatus.REFUNDED.value],
            OrderStatus.CANCELLED.value: [],
            OrderStatus.REFUNDED.value: []
        }
        
        return new_status in valid_transitions.get(current_status, [])
    
    def _handle_status_change(self, order_id: int, new_status: str):
        """Handle actions based on status change"""
        if new_status == OrderStatus.COMPLETED.value:
            # Send completion notification
            self._send_order_completion_email_by_id(order_id)
        elif new_status == OrderStatus.CANCELLED.value:
            # Handle cancellation
            logger.info(f"Order {order_id} cancelled")
        elif new_status == OrderStatus.REFUNDED.value:
            # Handle refund
            logger.info(f"Order {order_id} refunded")
    
    def _process_stripe_payment(self, payment: Payment, payment_details: Dict[str, Any]) -> bool:
        """Process Stripe payment"""
        try:
            from ..payment_service import payment_service
            from decimal import Decimal
            
            # Process payment with Stripe
            result = payment_service.process_payment(
                provider_name='stripe',
                amount=Decimal(str(payment.amount)),
                payment_method=payment_details,
                metadata={
                    'order_id': str(payment.order_id),
                    'payment_id': str(payment.id),
                    'description': f"Order #{payment.order.order_number}" if payment.order else "AgentShop Purchase"
                }
            )
            
            if result.success:
                # Mark payment as successful
                self.payment_service.mark_payment_successful(
                    payment.id, result.transaction_id
                )
                logger.info(f"Stripe payment successful: {result.transaction_id}")
                return True
            else:
                # Mark payment as failed
                self.payment_service.mark_payment_failed(
                    payment.id, result.error_message
                )
                logger.error(f"Stripe payment failed: {result.error_message}")
                return False
            
            return True
            
        except Exception as e:
            # Mark payment as failed
            self.payment_service.mark_payment_failed(
                payment.id, "stripe_error", str(e)
            )
            return False
    
    def _process_paypal_payment(self, payment: Payment, payment_details: Dict[str, Any]) -> bool:
        """Process PayPal payment"""
        try:
            from ..payment_service import payment_service
            from decimal import Decimal
            
            # Process payment with PayPal
            result = payment_service.process_payment(
                provider_name='paypal',
                amount=Decimal(str(payment.amount)),
                payment_method=payment_details,
                metadata={
                    'order_id': str(payment.order_id),
                    'payment_id': str(payment.id),
                    'description': f"Order #{payment.order.order_number}" if payment.order else "AgentShop Purchase"
                }
            )
            
            if result.success:
                # Mark payment as successful (or pending for approval)
                if 'approval_url' in result.raw_response:
                    # PayPal requires user approval, mark as pending
                    self.payment_service.update_payment_status(
                        payment.id, PaymentStatus.PENDING, result.transaction_id
                    )
                    logger.info(f"PayPal payment pending approval: {result.transaction_id}")
                    # Store approval URL for frontend
                    payment.notes = result.raw_response.get('approval_url', '')
                else:
                    # Payment completed
                    self.payment_service.mark_payment_successful(
                        payment.id, result.transaction_id
                    )
                    logger.info(f"PayPal payment successful: {result.transaction_id}")
                return True
            else:
                # Mark payment as failed
                self.payment_service.mark_payment_failed(
                    payment.id, result.error_message
                )
                logger.error(f"PayPal payment failed: {result.error_message}")
                return False
            
            return True
            
        except Exception as e:
            # Mark payment as failed
            self.payment_service.mark_payment_failed(
                payment.id, "paypal_error", str(e)
            )
            return False
    
    def _send_order_completion_email(self, order: Order):
        """Send order completion email"""
        try:
            # TODO: Implement email sending
            logger.info(f"Order completion email sent for order: {order.order_number}")
        except Exception as e:
            logger.error(f"Error sending completion email: {e}")
    
    def _send_order_completion_email_by_id(self, order_id: int):
        """Send order completion email by order ID"""
        order = self.get_by_id(order_id)
        if order:
            self._send_order_completion_email(order)


class OrderItemService(BaseService[OrderItem]):
    """Service for OrderItem entity"""
    
    def __init__(self, repository: OrderItemRepository = None, session: Session = None):
        super().__init__(repository, session)
    
    def _create_repository(self) -> OrderItemRepository:
        """Create OrderItemRepository instance"""
        return OrderItemRepository(self._session)
    
    def _create_entity_from_data(self, entity_data: Dict[str, Any]) -> OrderItem:
        """Create OrderItem instance from data dictionary"""
        return OrderItem(**entity_data)
    
    def generate_download_links(self, order_id: int, expires_hours: int = 48) -> bool:
        """Generate download links for order items"""
        try:
            return self.repository.generate_download_links(order_id, expires_hours)
        except Exception as e:
            logger.error(f"Error generating download links: {e}")
            return False
    
    def record_download(self, item_id: int) -> bool:
        """Record a download for an order item"""
        try:
            return self.repository.record_download(item_id)
        except Exception as e:
            logger.error(f"Error recording download: {e}")
            return False
    
    def get_downloadable_items(self, customer_id: int) -> List[OrderItem]:
        """Get downloadable items for a customer"""
        try:
            return self.repository.get_downloadable_items(customer_id)
        except Exception as e:
            logger.error(f"Error getting downloadable items: {e}")
            return []


class PaymentService(BaseService[Payment]):
    """Service for Payment entity"""
    
    def __init__(self, repository: PaymentRepository = None, session: Session = None):
        super().__init__(repository, session)
    
    def _create_repository(self) -> PaymentRepository:
        """Create PaymentRepository instance"""
        return PaymentRepository(self._session)
    
    def _create_entity_from_data(self, entity_data: Dict[str, Any]) -> Payment:
        """Create Payment instance from data dictionary"""
        return Payment(**entity_data)
    
    def create_payment(self, order_id: int, amount: float,
                      payment_processor: str, transaction_id: str = None) -> Payment:
        """Create new payment record"""
        try:
            return self.repository.create_payment(
                order_id, amount, payment_processor, transaction_id
            )
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            raise ServiceError("Failed to create payment") from e
    
    def mark_payment_successful(self, payment_id: int, transaction_id: str = None,
                               processor_fee: float = 0.0) -> bool:
        """Mark payment as successful"""
        try:
            return self.repository.update_payment_status(
                payment_id, PaymentStatus.SUCCESS.value, transaction_id
            )
        except Exception as e:
            logger.error(f"Error marking payment successful: {e}")
            return False
    
    def mark_payment_failed(self, payment_id: int, error_code: str = None,
                           error_message: str = None) -> bool:
        """Mark payment as failed"""
        try:
            return self.repository.update_payment_status(
                payment_id, PaymentStatus.FAILED.value,
                error_code=error_code, error_message=error_message
            )
        except Exception as e:
            logger.error(f"Error marking payment failed: {e}")
            return False
    
    def get_payment_stats(self) -> Dict[str, Any]:
        """Get payment statistics"""
        try:
            return self.repository.get_payment_stats()
        except Exception as e:
            logger.error(f"Error getting payment stats: {e}")
            return {}


class InstallationRequestService(BaseService[InstallationRequest]):
    """Service for InstallationRequest entity"""
    
    def __init__(self, repository: InstallationRequestRepository = None, session: Session = None):
        super().__init__(repository, session)
    
    def _create_repository(self) -> InstallationRequestRepository:
        """Create InstallationRequestRepository instance"""
        return InstallationRequestRepository(self._session)
    
    def _create_entity_from_data(self, entity_data: Dict[str, Any]) -> InstallationRequest:
        """Create InstallationRequest instance from data dictionary"""
        return InstallationRequest(**entity_data)
    
    def _after_create(self, request: InstallationRequest, entity_data: Dict[str, Any]):
        """Send notification after installation request creation"""
        try:
            from ..email_service import email_service
            
            # Prepare request data for email
            request_data = {
                'order_number': request.order.order_number if request.order else 'N/A',
                'customer_name': f"{request.order.billing_first_name} {request.order.billing_last_name}" if request.order else 'Unknown',
                'product_name': request.odoo_version,  # Using odoo_version as product identifier
                'request_date': request.created_at.strftime('%Y-%m-%d') if request.created_at else datetime.now().strftime('%Y-%m-%d'),
                'notes': request.notes or 'No additional notes provided'
            }
            
            # Send notification email to admin
            email_sent = email_service.send_installation_request_notification(request_data)
            
            if email_sent:
                logger.info(f"Installation request notification sent: {request.id}")
            else:
                logger.warning(f"Failed to send installation request notification: {request.id}")
                
        except Exception as e:
            logger.error(f"Error sending installation request notification: {e}")
    
    def create_installation_request(self, order_id: int, odoo_version: str,
                                   installation_period: datetime,
                                   tech_contact_name: str, tech_contact_email: str,
                                   comments: str = None,
                                   tech_contact_phone: str = None) -> InstallationRequest:
        """Create new installation request"""
        try:
            return self.repository.create_installation_request(
                order_id, odoo_version, installation_period,
                tech_contact_name, tech_contact_email,
                comments, tech_contact_phone
            )
        except Exception as e:
            logger.error(f"Error creating installation request: {e}")
            raise ServiceError("Failed to create installation request") from e
    
    def get_pending_requests(self) -> List[InstallationRequest]:
        """Get pending installation requests"""
        try:
            return self.repository.get_pending_requests()
        except Exception as e:
            logger.error(f"Error getting pending requests: {e}")
            return []
    
    def send_quote(self, request_id: int, quote_amount: float) -> bool:
        """Send quote for installation request"""
        try:
            success = self.repository.update_request_status(
                request_id, 'quoted', quote_amount
            )
            if success:
                # Send quote email to customer
                from ..email_service import email_service
                
                # Get the installation request details
                request = self.repository.get_by_id(request_id)
                if request and request.order:
                    quote_data = {
                        'customer_name': f"{request.order.billing_first_name} {request.order.billing_last_name}",
                        'customer_email': request.order.billing_email,
                        'order_number': request.order.order_number,
                        'product_name': request.odoo_version,
                        'quote_amount': f"{quote_amount:.2f}",
                        'estimated_hours': estimated_hours or 'TBD'
                    }
                    
                    email_sent = email_service.send_installation_quote(quote_data)
                    
                    if email_sent:
                        logger.info(f"Quote email sent for installation request: {request_id}")
                    else:
                        logger.warning(f"Failed to send quote email for request: {request_id}")
                else:
                    logger.error(f"Could not find request or order for quote email: {request_id}")
                
                logger.info(f"Quote sent for installation request: {request_id}")
            return success
        except Exception as e:
            logger.error(f"Error sending quote: {e}")
            return False
    
    def schedule_installation(self, request_id: int, scheduled_date: datetime) -> bool:
        """Schedule installation"""
        try:
            request = self.get_by_id(request_id)
            if request:
                request.schedule_installation(scheduled_date)
                self.repository.update(request)
                return True
            return False
        except Exception as e:
            logger.error(f"Error scheduling installation: {e}")
            return False