#!/usr/bin/env python3
"""
Authentication Controller - JWT-based authentication endpoints
Handles customer and admin login, registration, password reset, etc.
"""

from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity, get_jwt
)
from datetime import timedelta
import logging

from .base_controller import BaseController, handle_service_errors, rate_limit
from ...services.customer_service import CustomerService, CustomerSessionService
from ...services.admin_service import AdminUserService, AdminSessionService
from ..utils.validators import validate_email, validate_password_strength
from ..utils.exceptions import ValidationError, AuthenticationError

logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__)


class AuthController(BaseController):
    """Controller for Authentication endpoints"""
    
    def __init__(self):
        self.customer_service = CustomerService()
        self.customer_session_service = CustomerSessionService()
        self.admin_service = AdminUserService()
        self.admin_session_service = AdminSessionService()


# Initialize controller
controller = AuthController()


# Customer Authentication

@auth_bp.route('/register', methods=['POST'])
@handle_service_errors
@rate_limit("10/hour")
def register_customer():
    """
    Register new customer account
    
    Required fields:
        - email: Customer email address
        - password: Account password
        - first_name: Customer first name
        - last_name: Customer last name
    """
    data = controller.validate_json_request(
        required_fields=['email', 'password', 'first_name', 'last_name']
    )
    
    # Validate email format
    if not validate_email(data['email']):
        raise ValidationError("Invalid email format")
    
    # Validate password strength
    password_errors = validate_password_strength(data['password'], min_length=8)
    if password_errors:
        raise ValidationError("Password requirements not met", {'password': password_errors})
    
    # Get client information
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
    user_agent = request.headers.get('User-Agent', '')
    referral_source = request.headers.get('Referer', '')
    
    # Add client data to registration
    data.update({
        'ip_address': client_ip,
        'user_agent': user_agent,
        'referral_source': referral_source
    })
    
    # Register customer
    customer = controller.customer_service.register_customer(**data)
    
    # Create access and refresh tokens
    access_token = create_access_token(
        identity=customer.id,
        additional_claims={'is_admin': False, 'email': customer.email},
        expires_delta=timedelta(hours=24)
    )
    refresh_token = create_refresh_token(
        identity=customer.id,
        expires_delta=timedelta(days=30)
    )
    
    # Create customer session
    session = controller.customer_session_service.create_session(
        customer.id, client_ip, user_agent, refresh_token
    )
    
    return controller.success_response(
        data={
            'customer': {
                'id': customer.id,
                'email': customer.email,
                'first_name': customer.first_name,
                'last_name': customer.last_name,
                'email_verified': customer.email_verified
            },
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 86400  # 24 hours
        },
        message="Customer registered successfully",
        status_code=201
    )


@auth_bp.route('/login', methods=['POST'])
@handle_service_errors
@rate_limit("20/hour")
def login_customer():
    """
    Customer login
    
    Required fields:
        - email: Customer email address
        - password: Account password
    """
    data = controller.validate_json_request(
        required_fields=['email', 'password']
    )
    
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
    user_agent = request.headers.get('User-Agent', '')
    
    # Authenticate customer
    customer = controller.customer_service.authenticate_customer(
        email=data['email'],
        password=data['password'],
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    if not customer:
        return controller.error_response("Invalid credentials", 401)
    
    if not customer.is_active:
        return controller.error_response("Account is inactive", 401)
    
    # Create tokens
    access_token = create_access_token(
        identity=customer.id,
        additional_claims={'is_admin': False, 'email': customer.email},
        expires_delta=timedelta(hours=24)
    )
    refresh_token = create_refresh_token(
        identity=customer.id,
        expires_delta=timedelta(days=30)
    )
    
    # Update/create session
    session = controller.customer_session_service.create_session(
        customer.id, client_ip, user_agent, refresh_token
    )
    
    return controller.success_response(
        data={
            'customer': {
                'id': customer.id,
                'email': customer.email,
                'first_name': customer.first_name,
                'last_name': customer.last_name,
                'email_verified': customer.email_verified
            },
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 86400
        },
        message="Login successful"
    )


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
@handle_service_errors
@rate_limit("50/hour")
def refresh_token():
    """Refresh access token using refresh token"""
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    
    # Check if refresh token is still valid in database
    if not controller.customer_session_service.is_refresh_token_valid(current_user_id):
        return controller.error_response("Invalid refresh token", 401)
    
    # Create new access token
    access_token = create_access_token(
        identity=current_user_id,
        additional_claims={
            'is_admin': claims.get('is_admin', False),
            'email': claims.get('email', '')
        },
        expires_delta=timedelta(hours=24)
    )
    
    return controller.success_response(
        data={
            'access_token': access_token,
            'expires_in': 86400
        },
        message="Token refreshed successfully"
    )


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
@handle_service_errors
@rate_limit("100/hour")
def logout():
    """Logout and invalidate session"""
    current_user_id = get_jwt_identity()
    
    # Invalidate session
    controller.customer_session_service.invalidate_session(current_user_id)
    
    return controller.success_response(
        message="Logged out successfully"
    )


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
@handle_service_errors
@rate_limit("100/hour")
def get_current_user():
    """Get current authenticated user information"""
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    is_admin = claims.get('is_admin', False)
    
    if is_admin:
        user = controller.admin_service.get_by_id(current_user_id)
        if user:
            return controller.success_response(
                data={
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                    'is_admin': True,
                    'permissions': user.get_permissions() if hasattr(user, 'get_permissions') else []
                },
                message="Admin user retrieved successfully"
            )
    else:
        customer = controller.customer_service.get_by_id(current_user_id)
        if customer:
            return controller.success_response(
                data={
                    'id': customer.id,
                    'email': customer.email,
                    'first_name': customer.first_name,
                    'last_name': customer.last_name,
                    'email_verified': customer.email_verified,
                    'is_admin': False
                },
                message="Customer retrieved successfully"
            )
    
    return controller.error_response("User not found", 404)


# Password Reset

@auth_bp.route('/password-reset-request', methods=['POST'])
@handle_service_errors
@rate_limit("5/hour")
def request_password_reset():
    """
    Request password reset email
    
    Required fields:
        - email: Account email address
    """
    data = controller.validate_json_request(required_fields=['email'])
    
    # Validate email format
    if not validate_email(data['email']):
        raise ValidationError("Invalid email format")
    
    # Always return success to prevent email enumeration
    controller.customer_service.request_password_reset(data['email'])
    
    return controller.success_response(
        message="If an account with that email exists, a password reset link has been sent"
    )


@auth_bp.route('/password-reset-confirm', methods=['POST'])
@handle_service_errors
@rate_limit("10/hour")
def confirm_password_reset():
    """
    Confirm password reset with token and new password
    
    Required fields:
        - token: Password reset token
        - new_password: New account password
    """
    data = controller.validate_json_request(
        required_fields=['token', 'new_password']
    )
    
    # Validate new password strength
    password_errors = validate_password_strength(data['new_password'], min_length=8)
    if password_errors:
        raise ValidationError("Password requirements not met", {'password': password_errors})
    
    # Reset password
    success = controller.customer_service.reset_password(
        token=data['token'],
        new_password=data['new_password']
    )
    
    if not success:
        return controller.error_response("Invalid or expired reset token", 400)
    
    return controller.success_response(
        message="Password reset successful"
    )


# Email Verification

@auth_bp.route('/verify-email', methods=['POST'])
@handle_service_errors
@rate_limit("10/hour")
def verify_email():
    """
    Verify email address with token
    
    Required fields:
        - token: Email verification token
    """
    data = controller.validate_json_request(required_fields=['token'])
    
    # Verify email
    success = controller.customer_service.verify_email(data['token'])
    
    if not success:
        return controller.error_response("Invalid or expired verification token", 400)
    
    return controller.success_response(
        message="Email verified successfully"
    )


@auth_bp.route('/resend-verification', methods=['POST'])
@jwt_required()
@handle_service_errors
@rate_limit("3/hour")
def resend_verification():
    """Resend email verification (authenticated users only)"""
    current_user_id = get_jwt_identity()
    
    customer = controller.customer_service.get_by_id(current_user_id)
    if not customer:
        return controller.error_response("Customer not found", 404)
    
    if customer.email_verified:
        return controller.error_response("Email already verified", 400)
    
    # Resend verification email
    success = controller.customer_service.resend_verification_email(customer.id)
    
    if not success:
        return controller.error_response("Failed to send verification email", 400)
    
    return controller.success_response(
        message="Verification email sent"
    )


# Admin Authentication

@auth_bp.route('/admin/login', methods=['POST'])
@handle_service_errors
@rate_limit("10/hour")
def admin_login():
    """
    Admin user login
    
    Required fields:
        - email: Admin email address
        - password: Admin password
    """
    data = controller.validate_json_request(
        required_fields=['email', 'password']
    )
    
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
    user_agent = request.headers.get('User-Agent', '')
    
    # Authenticate admin
    admin = controller.admin_service.authenticate_admin(
        email=data['email'],
        password=data['password'],
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    if not admin:
        return controller.error_response("Invalid credentials", 401)
    
    if not admin.is_active:
        return controller.error_response("Account is inactive", 401)
    
    # Create tokens with admin claims
    access_token = create_access_token(
        identity=admin.id,
        additional_claims={
            'is_admin': True,
            'email': admin.email,
            'role': admin.role
        },
        expires_delta=timedelta(hours=8)  # Shorter session for admin
    )
    refresh_token = create_refresh_token(
        identity=admin.id,
        expires_delta=timedelta(days=7)  # Shorter refresh for admin
    )
    
    # Create admin session
    session = controller.admin_session_service.create_session(
        admin.id, client_ip, user_agent, refresh_token
    )
    
    return controller.success_response(
        data={
            'admin': {
                'id': admin.id,
                'email': admin.email,
                'first_name': admin.first_name,
                'last_name': admin.last_name,
                'role': admin.role
            },
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 28800  # 8 hours
        },
        message="Admin login successful"
    )


@auth_bp.route('/admin/logout', methods=['POST'])
@jwt_required()
@handle_service_errors
@rate_limit("100/hour")
def admin_logout():
    """Admin logout"""
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    
    if not claims.get('is_admin', False):
        return controller.error_response("Admin access required", 403)
    
    # Invalidate admin session
    controller.admin_session_service.invalidate_session(current_user_id)
    
    return controller.success_response(
        message="Admin logged out successfully"
    )


# Account Management

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
@handle_service_errors
@rate_limit("5/hour")
def change_password():
    """
    Change password for authenticated user
    
    Required fields:
        - current_password: Current account password
        - new_password: New account password
    """
    data = controller.validate_json_request(
        required_fields=['current_password', 'new_password']
    )
    
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    is_admin = claims.get('is_admin', False)
    
    # Validate new password strength
    min_length = 12 if is_admin else 8
    password_errors = validate_password_strength(data['new_password'], min_length=min_length)
    if password_errors:
        raise ValidationError("Password requirements not met", {'password': password_errors})
    
    if is_admin:
        success = controller.admin_service.change_password(
            current_user_id,
            data['current_password'],
            data['new_password']
        )
    else:
        success = controller.customer_service.change_password(
            current_user_id,
            data['current_password'],
            data['new_password']
        )
    
    if not success:
        return controller.error_response("Current password is incorrect", 400)
    
    return controller.success_response(
        message="Password changed successfully"
    )