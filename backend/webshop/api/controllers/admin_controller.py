#!/usr/bin/env python3
"""
Admin Controller - REST API endpoints for admin operations
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from .base_controller import (
    BaseController, require_admin, 
    handle_service_errors, rate_limit
)
from ...services.admin_service import AdminUserService, ConfigurationService, EmailTemplateService
from ..utils.serializers import AdminUserSerializer

logger = logging.getLogger(__name__)

# Create blueprint
admin_bp = Blueprint('admin', __name__)


class AdminController(BaseController):
    """Controller for Admin operations"""
    
    def __init__(self):
        self.admin_service = AdminUserService()
        self.config_service = ConfigurationService()
        self.template_service = EmailTemplateService()
        self.serializer = AdminUserSerializer()


# Initialize controller
controller = AdminController()


# Admin User Management

@admin_bp.route('/users', methods=['GET'])
@require_admin
@handle_service_errors
@rate_limit("50/hour")
def get_admin_users():
    """Get list of admin users"""
    page, per_page = controller.get_pagination_params()
    search_params = controller.get_search_params()
    
    if search_params['search']:
        users = controller.admin_service.search(
            search_term=search_params['search'],
            limit=per_page
        )
    else:
        users = controller.admin_service.get_all(
            limit=per_page,
            offset=(page - 1) * per_page,
            order_by=search_params['sort_by'],
            order_desc=search_params['sort_order'] == 'desc'
        )
    
    serialized_users = [
        controller.serializer.serialize(user, include_sensitive=True) 
        for user in users
    ]
    
    return controller.paginated_response(
        items=serialized_users,
        total=len(users),
        page=page,
        per_page=per_page,
        message=f"Found {len(users)} admin users"
    )


@admin_bp.route('/users', methods=['POST'])
@require_admin
@handle_service_errors
@rate_limit("10/hour")
def create_admin_user():
    """Create new admin user"""
    data = controller.validate_json_request(
        required_fields=['email', 'password', 'first_name', 'last_name', 'role']
    )
    
    admin_user = controller.admin_service.create_admin_user(**data)
    
    return controller.success_response(
        data=controller.serializer.serialize(admin_user),
        message="Admin user created successfully",
        status_code=201
    )


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@require_admin
@handle_service_errors
@rate_limit("20/hour")
def update_admin_user(user_id: int):
    """Update admin user"""
    data = controller.validate_json_request()
    
    # Remove password from updates (use separate endpoint)
    data.pop('password', None)
    
    user = controller.admin_service.update(user_id, data)
    
    if not user:
        return controller.error_response("Admin user not found", 404)
    
    return controller.success_response(
        data=controller.serializer.serialize(user),
        message="Admin user updated successfully"
    )


# System Configuration

@admin_bp.route('/config', methods=['GET'])
@require_admin
@handle_service_errors
@rate_limit("50/hour")
def get_configuration():
    """Get system configuration"""
    config = controller.config_service.get_all_settings()
    
    return controller.success_response(
        data=config,
        message="Configuration retrieved successfully"
    )


@admin_bp.route('/config', methods=['PUT'])
@require_admin
@handle_service_errors
@rate_limit("20/hour")
def update_configuration():
    """Update system configuration"""
    data = controller.validate_json_request()
    
    success = controller.config_service.update_multiple_settings(data)
    
    if not success:
        return controller.error_response("Failed to update configuration", 400)
    
    return controller.success_response(
        message="Configuration updated successfully"
    )


@admin_bp.route('/config/<string:key>', methods=['PUT'])
@require_admin
@handle_service_errors
@rate_limit("50/hour")
def update_config_setting(key: str):
    """Update single configuration setting"""
    data = controller.validate_json_request(
        required_fields=['value']
    )
    
    success = controller.config_service.set_setting(
        key, 
        data['value'],
        description=data.get('description')
    )
    
    if not success:
        return controller.error_response("Failed to update setting", 400)
    
    return controller.success_response(
        message=f"Setting '{key}' updated successfully"
    )


# Email Templates

@admin_bp.route('/email-templates', methods=['GET'])
@require_admin
@handle_service_errors
@rate_limit("50/hour")
def get_email_templates():
    """Get email templates"""
    templates = controller.template_service.get_all()
    
    # Convert to dict format
    serialized_templates = [template.to_dict() for template in templates]
    
    return controller.success_response(
        data=serialized_templates,
        message=f"Found {len(templates)} email templates"
    )


@admin_bp.route('/email-templates', methods=['POST'])
@require_admin
@handle_service_errors
@rate_limit("20/hour")
def create_email_template():
    """Create email template"""
    data = controller.validate_json_request(
        required_fields=['name', 'subject', 'html_body']
    )
    
    template = controller.template_service.create(data)
    
    return controller.success_response(
        data=template.to_dict(),
        message="Email template created successfully",
        status_code=201
    )


@admin_bp.route('/email-templates/<int:template_id>', methods=['PUT'])
@require_admin
@handle_service_errors
@rate_limit("50/hour")
def update_email_template(template_id: int):
    """Update email template"""
    data = controller.validate_json_request()
    
    template = controller.template_service.update(template_id, data)
    
    if not template:
        return controller.error_response("Email template not found", 404)
    
    return controller.success_response(
        data=template.to_dict(),
        message="Email template updated successfully"
    )


# System Statistics and Reports

@admin_bp.route('/dashboard', methods=['GET'])
@require_admin
@handle_service_errors
@rate_limit("50/hour")
def get_dashboard_stats():
    """Get dashboard statistics"""
    # This would aggregate stats from various services
    stats = {
        'total_customers': controller.admin_service.get_customer_count(),
        'total_orders': controller.admin_service.get_order_count(),
        'total_products': controller.admin_service.get_product_count(),
        'pending_support_requests': controller.admin_service.get_pending_support_count(),
        'recent_activity': controller.admin_service.get_recent_activity()
    }
    
    return controller.success_response(
        data=stats,
        message="Dashboard statistics retrieved successfully"
    )


@admin_bp.route('/reports/sales', methods=['GET'])
@require_admin
@handle_service_errors
@rate_limit("20/hour")
def get_sales_report():
    """Get sales report"""
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    report = controller.admin_service.get_sales_report(date_from, date_to)
    
    return controller.success_response(
        data=report,
        message="Sales report generated successfully"
    )