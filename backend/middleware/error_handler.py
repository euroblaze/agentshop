import logging
import traceback
from flask import jsonify, request
from typing import Dict, Any


class ErrorHandler:
    """Centralized error handling for the application"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize error handlers for Flask app"""
        app.errorhandler(400)(self.handle_bad_request)
        app.errorhandler(401)(self.handle_unauthorized)
        app.errorhandler(403)(self.handle_forbidden)
        app.errorhandler(404)(self.handle_not_found)
        app.errorhandler(429)(self.handle_rate_limit)
        app.errorhandler(500)(self.handle_internal_error)
        app.errorhandler(Exception)(self.handle_generic_exception)
    
    def handle_bad_request(self, error):
        """Handle 400 Bad Request errors"""
        return jsonify({
            "success": False,
            "data": None,
            "message": "Bad request. Please check your input.",
            "errors": ["bad_request"]
        }), 400
    
    def handle_unauthorized(self, error):
        """Handle 401 Unauthorized errors"""
        return jsonify({
            "success": False,
            "data": None,
            "message": "Authentication required.",
            "errors": ["unauthorized"]
        }), 401
    
    def handle_forbidden(self, error):
        """Handle 403 Forbidden errors"""
        return jsonify({
            "success": False,
            "data": None,
            "message": "Access forbidden.",
            "errors": ["forbidden"]
        }), 403
    
    def handle_not_found(self, error):
        """Handle 404 Not Found errors"""
        return jsonify({
            "success": False,
            "data": None,
            "message": "Resource not found.",
            "errors": ["not_found"]
        }), 404
    
    def handle_rate_limit(self, error):
        """Handle 429 Rate Limit errors"""
        return jsonify({
            "success": False,
            "data": None,
            "message": "Rate limit exceeded. Please try again later.",
            "errors": ["rate_limit_exceeded"]
        }), 429
    
    def handle_internal_error(self, error):
        """Handle 500 Internal Server errors"""
        logging.error(f"Internal server error: {str(error)}")
        logging.error(traceback.format_exc())
        
        return jsonify({
            "success": False,
            "data": None,
            "message": "Internal server error occurred.",
            "errors": ["internal_server_error"]
        }), 500
    
    def handle_generic_exception(self, error):
        """Handle any unhandled exceptions"""
        logging.error(f"Unhandled exception: {str(error)}")
        logging.error(traceback.format_exc())
        
        # Check if it's an LLM-related error
        if "LLM" in str(error) or "generation" in str(error).lower():
            return self.handle_llm_error(error)
        
        return jsonify({
            "success": False,
            "data": None,
            "message": "An unexpected error occurred.",
            "errors": ["unexpected_error"]
        }), 500
    
    def handle_llm_error(self, error):
        """Handle LLM-specific errors"""
        error_message = str(error)
        
        # Categorize LLM errors
        if "API key" in error_message or "authentication" in error_message.lower():
            return jsonify({
                "success": False,
                "data": None,
                "message": "LLM provider authentication failed. Please check your API keys.",
                "errors": ["llm_auth_error"]
            }), 401
        
        elif "quota" in error_message.lower() or "limit" in error_message.lower():
            return jsonify({
                "success": False,
                "data": None,
                "message": "LLM provider quota or rate limit exceeded.",
                "errors": ["llm_quota_error"]
            }), 429
        
        elif "timeout" in error_message.lower():
            return jsonify({
                "success": False,
                "data": None,
                "message": "LLM request timed out. Please try again.",
                "errors": ["llm_timeout_error"]
            }), 504
        
        elif "model" in error_message.lower() and "not found" in error_message.lower():
            return jsonify({
                "success": False,
                "data": None,
                "message": "Requested LLM model is not available.",
                "errors": ["llm_model_error"]
            }), 400
        
        else:
            return jsonify({
                "success": False,
                "data": None,
                "message": f"LLM service error: {error_message}",
                "errors": ["llm_service_error"]
            }), 500


def setup_error_handling(app):
    """Setup error handling for the Flask application"""
    error_handler = ErrorHandler(app)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    return error_handler