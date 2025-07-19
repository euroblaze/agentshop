#!/usr/bin/env python3
"""
Orders Controller - REST API endpoints for order management
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import logging

from .base_controller import (
    BaseController, require_auth, require_admin, 
    handle_service_errors, rate_limit
)
from ...services.order_service import OrderService, OrderItemService, PaymentService
from ..utils.serializers import OrderSerializer, OrderItemSerializer, PaymentSerializer

logger = logging.getLogger(__name__)

# Create blueprint
orders_bp = Blueprint('orders', __name__)


class OrdersController(BaseController):
    """Controller for Order-related endpoints"""
    
    def __init__(self):
        self.order_service = OrderService()
        self.order_item_service = OrderItemService()
        self.payment_service = PaymentService()
        self.order_serializer = OrderSerializer()
        self.item_serializer = OrderItemSerializer()
        self.payment_serializer = PaymentSerializer()


# Initialize controller
controller = OrdersController()


# Customer Order Endpoints

@orders_bp.route('/', methods=['POST'])
@require_auth
@handle_service_errors
@rate_limit("20/hour")
def create_order():
    """Create new order"""
    customer_id = get_jwt_identity()
    data = controller.validate_json_request(
        required_fields=['billing_info', 'cart_items']
    )
    
    order = controller.order_service.create_order(
        customer_id=customer_id,
        billing_info=data['billing_info'],
        cart_items=data.get('cart_items', [])
    )
    
    return controller.success_response(
        data=controller.order_serializer.serialize(order),
        message="Order created successfully",
        status_code=201
    )


@orders_bp.route('/', methods=['GET'])
@require_auth
@handle_service_errors
@rate_limit("100/hour")
def get_customer_orders():
    """Get customer's orders"""
    customer_id = get_jwt_identity()
    page, per_page = controller.get_pagination_params()
    
    orders = controller.order_service.get_customer_orders(
        customer_id,
        limit=per_page,
        offset=(page - 1) * per_page
    )
    
    serialized_orders = [controller.order_serializer.serialize(order) for order in orders]
    
    return controller.paginated_response(
        items=serialized_orders,
        total=len(orders),  # Simplified
        page=page,
        per_page=per_page,
        message=f"Found {len(orders)} orders"
    )


@orders_bp.route('/<int:order_id>', methods=['GET'])
@require_auth
@handle_service_errors
@rate_limit("100/hour")
def get_order(order_id: int):
    """Get order details"""
    customer_id = get_jwt_identity()
    claims = get_jwt()
    is_admin = claims.get('is_admin', False)
    
    order = controller.order_service.get_by_id(order_id)
    
    if not order:
        return controller.error_response("Order not found", 404)
    
    # Check ownership (customers can only see their own orders)
    if not is_admin and order.customer_id != customer_id:
        return controller.error_response("Access denied", 403)
    
    return controller.success_response(
        data=controller.order_serializer.serialize(order),
        message="Order retrieved successfully"
    )


@orders_bp.route('/<int:order_id>/items', methods=['GET'])
@require_auth
@handle_service_errors
@rate_limit("100/hour")
def get_order_items(order_id: int):
    """Get order items"""
    customer_id = get_jwt_identity()
    claims = get_jwt()
    is_admin = claims.get('is_admin', False)
    
    # Verify order access
    order = controller.order_service.get_by_id(order_id)
    if not order:
        return controller.error_response("Order not found", 404)
    
    if not is_admin and order.customer_id != customer_id:
        return controller.error_response("Access denied", 403)
    
    items = controller.order_item_service.get_order_items(order_id)
    serialized_items = [controller.item_serializer.serialize(item) for item in items]
    
    return controller.success_response(
        data=serialized_items,
        message=f"Found {len(items)} order items"
    )


@orders_bp.route('/<int:order_id>/download-links', methods=['POST'])
@require_auth
@handle_service_errors
@rate_limit("50/hour")
def generate_download_links(order_id: int):
    """Generate download links for paid order"""
    customer_id = get_jwt_identity()
    
    # Verify order ownership and payment status
    order = controller.order_service.get_by_id(order_id)
    if not order:
        return controller.error_response("Order not found", 404)
    
    if order.customer_id != customer_id:
        return controller.error_response("Access denied", 403)
    
    if order.status != 'paid':
        return controller.error_response("Order must be paid to generate download links", 400)
    
    # Generate download links
    success = controller.order_item_service.generate_download_links(order_id)
    
    if not success:
        return controller.error_response("Failed to generate download links", 400)
    
    return controller.success_response(
        message="Download links generated successfully"
    )


@orders_bp.route('/items/<int:item_id>/download', methods=['GET'])
@require_auth
@handle_service_errors
@rate_limit("100/hour")
def download_item(item_id: int):
    """Download order item"""
    customer_id = get_jwt_identity()
    
    # Get download URL and verify access
    download_url = controller.order_item_service.get_download_url(item_id, customer_id)
    
    if not download_url:
        return controller.error_response("Download not available", 404)
    
    # Record download
    controller.order_item_service.record_download(item_id)
    
    return controller.success_response(
        data={'download_url': download_url},
        message="Download URL retrieved successfully"
    )


# Payment Endpoints

@orders_bp.route('/<int:order_id>/payments', methods=['POST'])
@require_auth
@handle_service_errors
@rate_limit("10/hour")
def process_payment():
    """Process order payment"""
    customer_id = get_jwt_identity()
    order_id = request.view_args['order_id']
    
    data = controller.validate_json_request(
        required_fields=['processor', 'payment_data']
    )
    
    # Verify order ownership
    order = controller.order_service.get_by_id(order_id)
    if not order:
        return controller.error_response("Order not found", 404)
    
    if order.customer_id != customer_id:
        return controller.error_response("Access denied", 403)
    
    # Process payment
    payment = controller.payment_service.process_payment(
        order_id=order_id,
        processor=data['processor'],
        payment_data=data['payment_data']
    )
    
    if not payment:
        return controller.error_response("Payment processing failed", 400)
    
    return controller.success_response(
        data=controller.payment_serializer.serialize(payment),
        message="Payment processed successfully"
    )


@orders_bp.route('/<int:order_id>/payments', methods=['GET'])
@require_auth
@handle_service_errors
@rate_limit("100/hour")
def get_order_payments(order_id: int):
    """Get order payments"""
    customer_id = get_jwt_identity()
    claims = get_jwt()
    is_admin = claims.get('is_admin', False)
    
    # Verify order access
    order = controller.order_service.get_by_id(order_id)
    if not order:
        return controller.error_response("Order not found", 404)
    
    if not is_admin and order.customer_id != customer_id:
        return controller.error_response("Access denied", 403)
    
    payments = controller.payment_service.get_order_payments(order_id)
    serialized_payments = [controller.payment_serializer.serialize(payment) for payment in payments]
    
    return controller.success_response(
        data=serialized_payments,
        message=f"Found {len(payments)} payments"
    )


# Admin Order Management

@orders_bp.route('/admin/orders', methods=['GET'])
@require_admin
@handle_service_errors
@rate_limit("100/hour")
def get_all_orders():
    """Get all orders (admin only)"""
    page, per_page = controller.get_pagination_params()
    search_params = controller.get_search_params()
    
    # Apply filters
    filters = {}
    if 'status' in search_params['filters']:
        filters['status'] = search_params['filters']['status']
    
    if search_params['search']:
        orders = controller.order_service.search(
            search_term=search_params['search'],
            limit=per_page
        )
    else:
        orders = controller.order_service.get_all(
            filters=filters,
            limit=per_page,
            offset=(page - 1) * per_page,
            order_by=search_params['sort_by'],
            order_desc=search_params['sort_order'] == 'desc'
        )
    
    serialized_orders = [controller.order_serializer.serialize(order) for order in orders]
    
    return controller.paginated_response(
        items=serialized_orders,
        total=len(orders),  # Simplified
        page=page,
        per_page=per_page,
        message=f"Found {len(orders)} orders"
    )


@orders_bp.route('/<int:order_id>/status', methods=['PUT'])
@require_admin
@handle_service_errors
@rate_limit("100/hour")
def update_order_status(order_id: int):
    """Update order status (admin only)"""
    data = controller.validate_json_request(
        required_fields=['status']
    )
    
    success = controller.order_service.update_order_status(
        order_id, 
        data['status'],
        admin_notes=data.get('admin_notes')
    )
    
    if not success:
        return controller.error_response("Failed to update order status", 400)
    
    return controller.success_response(
        message="Order status updated successfully"
    )


@orders_bp.route('/stats', methods=['GET'])
@require_admin
@handle_service_errors
@rate_limit("20/hour")
def get_order_stats():
    """Get order statistics (admin only)"""
    stats = controller.order_service.get_order_statistics()
    
    return controller.success_response(
        data=stats,
        message="Order statistics retrieved successfully"
    )