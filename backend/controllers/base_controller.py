#!/usr/bin/env python3
"""
Base Controller - Common controller functionality
"""

from flask import request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from functools import wraps
from typing import Dict, Any, Optional, List, Union
import logging

logger = logging.getLogger(__name__)


class BaseController:
    """Base controller with common functionality"""
    
    def __init__(self):
        self.logger = logger
    
    def success_response(self, data: Any = None, message: str = "Success", status_code: int = 200) -> tuple:
        """Return standardized success response"""
        response = {
            "success": True,
            "message": message,
            "data": data
        }
        return jsonify(response), status_code
    
    def error_response(self, message: str = "Error", status_code: int = 400, errors: Optional[Dict] = None) -> tuple:
        """Return standardized error response"""
        response = {
            "success": False,
            "message": message,
            "errors": errors or {}
        }
        return jsonify(response), status_code
    
    def paginated_response(self, items: List[Any], total: int, page: int, per_page: int, message: str = "Success") -> tuple:
        """Return paginated response"""
        response = {
            "success": True,
            "message": message,
            "data": items,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page,
                "has_next": page * per_page < total,
                "has_prev": page > 1
            }
        }
        return jsonify(response), 200
    
    def get_pagination_params(self) -> tuple:
        """Extract pagination parameters from request"""
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 items per page
        return page, per_page
    
    def get_current_user_id(self) -> Optional[int]:
        """Get current authenticated user ID"""
        try:
            verify_jwt_in_request(optional=True)
            identity = get_jwt_identity()
            return int(identity) if identity else None
        except:
            return None
    
    def validate_json_request(self, required_fields: List[str] = None) -> Dict[str, Any]:
        """Validate JSON request and check required fields"""
        if not request.is_json:
            raise ValueError("Request must be JSON")
        
        data = request.get_json()
        if not data:
            raise ValueError("Request body cannot be empty")
        
        if required_fields:
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        return data


def auth_required(f):
    """Decorator for routes that require authentication"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator for routes that require admin privileges"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        # Get current user and check admin status
        from ..services.customer_service import CustomerService
        
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        try:
            customer_service = CustomerService()
            customer = customer_service.get_by_id(int(current_user_id))
            
            if not customer or not customer.is_admin:
                return jsonify({"error": "Admin privileges required"}), 403
                
        except Exception as e:
            logger.error(f"Admin check error: {e}")
            return jsonify({"error": "Authorization check failed"}), 500
        
        return f(*args, **kwargs)
    return decorated_function


def handle_exceptions(f):
    """Decorator for handling common exceptions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Validation error in {f.__name__}: {e}")
            return jsonify({"success": False, "message": str(e)}), 400
        except PermissionError as e:
            logger.warning(f"Permission error in {f.__name__}: {e}")
            return jsonify({"success": False, "message": "Insufficient permissions"}), 403
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {e}")
            return jsonify({"success": False, "message": "Internal server error"}), 500
    return decorated_function


class APIResponse:
    """Helper class for API responses"""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", status_code: int = 200):
        """Return success response"""
        return jsonify({
            "success": True,
            "message": message,
            "data": data
        }), status_code
    
    @staticmethod
    def error(message: str = "Error", status_code: int = 400, errors: Optional[Dict] = None):
        """Return error response"""
        return jsonify({
            "success": False,
            "message": message,
            "errors": errors or {}
        }), status_code
    
    @staticmethod
    def paginated(items: List[Any], total: int, page: int, per_page: int, message: str = "Success"):
        """Return paginated response"""
        return jsonify({
            "success": True,
            "message": message,
            "data": items,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page,
                "has_next": page * per_page < total,
                "has_prev": page > 1
            }
        }), 200