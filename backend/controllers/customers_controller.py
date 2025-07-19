#!/usr/bin/env python3
"""
Customers Controller - REST API endpoints for customer management
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from .base_controller import (
    BaseController, require_auth, require_admin, 
    handle_service_errors, rate_limit
)
from ...services.customer_service import CustomerService, SupportRequestService
from ..utils.serializers import CustomerSerializer, SupportRequestSerializer

logger = logging.getLogger(__name__)

# Create blueprint
customers_bp = Blueprint('customers', __name__)


class CustomersController(BaseController):
    """Controller for Customer-related endpoints"""
    
    def __init__(self):
        self.customer_service = CustomerService()
        self.support_service = SupportRequestService()
        self.serializer = CustomerSerializer()
        self.support_serializer = SupportRequestSerializer()


# Initialize controller
controller = CustomersController()


# Customer Profile Management

@customers_bp.route('/profile', methods=['GET'])
@require_auth
@handle_service_errors
@rate_limit("100/hour")
def get_customer_profile():
    """Get current customer profile"""
    customer_id = get_jwt_identity()
    customer = controller.customer_service.get_by_id(customer_id)
    
    if not customer:
        return controller.error_response("Customer not found", 404)
    
    return controller.success_response(
        data=controller.serializer.serialize(customer),
        message="Profile retrieved successfully"
    )


@customers_bp.route('/profile', methods=['PUT'])
@require_auth
@handle_service_errors
@rate_limit("20/hour")
def update_customer_profile():
    """Update customer profile"""
    customer_id = get_jwt_identity()
    data = controller.validate_json_request()
    
    # Remove sensitive fields that shouldn't be updated via this endpoint
    sensitive_fields = ['email', 'password', 'is_active', 'email_verified']
    for field in sensitive_fields:
        data.pop(field, None)
    
    customer = controller.customer_service.update(customer_id, data)
    
    if not customer:
        return controller.error_response("Customer not found", 404)
    
    return controller.success_response(
        data=controller.serializer.serialize(customer),
        message="Profile updated successfully"
    )


# Customer Support

@customers_bp.route('/support/requests', methods=['POST'])
@require_auth
@handle_service_errors
@rate_limit("10/hour")
def create_support_request():
    """Create new support request"""
    customer_id = get_jwt_identity()
    data = controller.validate_json_request(
        required_fields=['subject', 'message']
    )
    
    # Add customer ID to request data
    data['customer_id'] = customer_id
    
    support_request = controller.support_service.create(data)
    
    return controller.success_response(
        data=controller.support_serializer.serialize(support_request),
        message="Support request created successfully",
        status_code=201
    )


@customers_bp.route('/support/requests', methods=['GET'])
@require_auth
@handle_service_errors
@rate_limit("50/hour")
def get_customer_support_requests():
    """Get customer's support requests"""
    customer_id = get_jwt_identity()
    page, per_page = controller.get_pagination_params()
    
    requests = controller.support_service.get_customer_requests(
        customer_id, 
        limit=per_page,
        offset=(page - 1) * per_page
    )
    
    serialized_requests = [controller.support_serializer.serialize(req) for req in requests]
    
    return controller.paginated_response(
        items=serialized_requests,
        total=len(requests),  # Simplified
        page=page,
        per_page=per_page,
        message=f"Found {len(requests)} support requests"
    )


@customers_bp.route('/support/requests/<int:request_id>', methods=['GET'])
@require_auth
@handle_service_errors
@rate_limit("100/hour")
def get_support_request(request_id: int):
    """Get specific support request"""
    customer_id = get_jwt_identity()
    support_request = controller.support_service.get_by_id(request_id)
    
    if not support_request:
        return controller.error_response("Support request not found", 404)
    
    # Verify ownership
    if support_request.customer_id != customer_id:
        return controller.error_response("Access denied", 403)
    
    return controller.success_response(
        data=controller.support_serializer.serialize(support_request),
        message="Support request retrieved successfully"
    )


# Admin Customer Management

@customers_bp.route('/', methods=['GET'])
@require_admin
@handle_service_errors
@rate_limit("100/hour")
def get_customers():
    """Get paginated list of customers (admin only)"""
    page, per_page = controller.get_pagination_params()
    search_params = controller.get_search_params()
    
    if search_params['search']:
        customers = controller.customer_service.search(
            search_term=search_params['search'],
            limit=per_page
        )
    else:
        customers = controller.customer_service.get_all(
            limit=per_page,
            offset=(page - 1) * per_page,
            order_by=search_params['sort_by'],
            order_desc=search_params['sort_order'] == 'desc'
        )
    
    serialized_customers = [
        controller.serializer.serialize(customer, include_sensitive=True) 
        for customer in customers
    ]
    
    return controller.paginated_response(
        items=serialized_customers,
        total=len(customers),  # Simplified
        page=page,
        per_page=per_page,
        message=f"Found {len(customers)} customers"
    )


@customers_bp.route('/<int:customer_id>', methods=['GET'])
@require_admin
@handle_service_errors
@rate_limit("100/hour")
def get_customer(customer_id: int):
    """Get customer by ID (admin only)"""
    customer = controller.customer_service.get_by_id(customer_id)
    
    if not customer:
        return controller.error_response("Customer not found", 404)
    
    return controller.success_response(
        data=controller.serializer.serialize(customer, include_sensitive=True),
        message="Customer retrieved successfully"
    )


@customers_bp.route('/<int:customer_id>/deactivate', methods=['POST'])
@require_admin
@handle_service_errors
@rate_limit("50/hour")
def deactivate_customer(customer_id: int):
    """Deactivate customer account (admin only)"""
    success = controller.customer_service.deactivate_customer(customer_id)
    
    if not success:
        return controller.error_response("Failed to deactivate customer", 400)
    
    return controller.success_response(
        message="Customer account deactivated successfully"
    )


@customers_bp.route('/<int:customer_id>/activate', methods=['POST'])
@require_admin
@handle_service_errors
@rate_limit("50/hour")
def activate_customer(customer_id: int):
    """Activate customer account (admin only)"""
    success = controller.customer_service.activate_customer(customer_id)
    
    if not success:
        return controller.error_response("Failed to activate customer", 400)
    
    return controller.success_response(
        message="Customer account activated successfully"
    )