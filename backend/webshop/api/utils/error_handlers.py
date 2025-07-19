#!/usr/bin/env python3
"""
Global error handlers for Flask API
"""

from flask import jsonify, request
from flask_jwt_extended import JWTManager
from werkzeug.exceptions import HTTPException
import logging

from .exceptions import APIError, ValidationError, AuthenticationError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Register global error handlers for the Flask app"""
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle validation errors"""
        logger.warning(f"Validation error: {error.message}")
        return jsonify({
            'success': False,
            'message': error.message,
            'errors': error.errors
        }), 400
    
    @app.errorhandler(AuthenticationError)
    def handle_authentication_error(error):
        """Handle authentication errors"""
        logger.warning(f"Authentication error: {error.message}")
        return jsonify({
            'success': False,
            'message': error.message
        }), 401
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handle generic API errors"""
        logger.error(f"API error: {error.message}")
        return jsonify({
            'success': False,
            'message': error.message
        }), error.status_code
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle HTTP exceptions"""
        logger.warning(f"HTTP error {error.code}: {error.description}")
        return jsonify({
            'success': False,
            'message': error.description,
            'error_code': error.code
        }), error.code
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 errors"""
        return jsonify({
            'success': False,
            'message': 'Resource not found',
            'error_code': 404
        }), 404
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Handle 405 Method Not Allowed"""
        return jsonify({
            'success': False,
            'message': 'Method not allowed',
            'error_code': 405
        }), 405
    
    @app.errorhandler(429)
    def handle_rate_limit_exceeded(error):
        """Handle rate limit exceeded"""
        return jsonify({
            'success': False,
            'message': 'Rate limit exceeded',
            'error_code': 429
        }), 429
    
    @app.errorhandler(500)
    def handle_internal_server_error(error):
        """Handle internal server errors"""
        logger.error(f"Internal server error: {str(error)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error_code': 500
        }), 500
    
    # JWT error handlers
    @app.errorhandler(JWTManager.expired_token_callback)
    def handle_expired_token(jwt_header, jwt_payload):
        """Handle expired JWT tokens"""
        return jsonify({
            'success': False,
            'message': 'Token has expired',
            'error_code': 'TOKEN_EXPIRED'
        }), 401
    
    @app.errorhandler(JWTManager.invalid_token_callback)
    def handle_invalid_token(error_message):
        """Handle invalid JWT tokens"""
        return jsonify({
            'success': False,
            'message': 'Invalid token',
            'error_code': 'INVALID_TOKEN'
        }), 401
    
    @app.errorhandler(JWTManager.unauthorized_callback)
    def handle_unauthorized(error_message):
        """Handle missing JWT tokens"""
        return jsonify({
            'success': False,
            'message': 'Authorization token required',
            'error_code': 'TOKEN_REQUIRED'
        }), 401
    
    @app.errorhandler(JWTManager.needs_fresh_token_callback)
    def handle_needs_fresh_token(jwt_header, jwt_payload):
        """Handle requests requiring fresh tokens"""
        return jsonify({
            'success': False,
            'message': 'Fresh token required',
            'error_code': 'FRESH_TOKEN_REQUIRED'
        }), 401
    
    @app.errorhandler(JWTManager.revoked_token_callback)
    def handle_revoked_token(jwt_header, jwt_payload):
        """Handle revoked JWT tokens"""
        return jsonify({
            'success': False,
            'message': 'Token has been revoked',
            'error_code': 'TOKEN_REVOKED'
        }), 401
    
    # Handle exceptions during JSON parsing
    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle bad request errors (usually JSON parsing errors)"""
        if 'application/json' in request.content_type:
            return jsonify({
                'success': False,
                'message': 'Invalid JSON in request body',
                'error_code': 400
            }), 400
        else:
            return jsonify({
                'success': False,
                'message': 'Bad request',
                'error_code': 400
            }), 400