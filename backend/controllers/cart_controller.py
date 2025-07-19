#!/usr/bin/env python3
"""
Shopping Cart Controller - Handles shopping cart operations
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from typing import Dict, Any, List, Optional
import logging

# Import core API components
try:
    from ..core.api.base_controller import BaseController, handle_api_errors, get_paginated_results
    from ..core.api.response_serializer import ResponseSerializer
    from ..core.validation.validators import validate_required_fields, ValidationError
    from ..services.webshop.cart_service import CartService
    from ..models.cart_models import CartItem
except ImportError:
    # Fallback for import issues during development
    from core.api.base_controller import BaseController, handle_api_errors, get_paginated_results
    from core.api.response_serializer import ResponseSerializer
    from core.validation.validators import validate_required_fields, ValidationError
    from services.webshop.cart_service import CartService
    from models.cart_models import CartItem

logger = logging.getLogger(__name__)

# Create Blueprint
cart_bp = Blueprint('cart', __name__, url_prefix='/api/cart')


class CartController(BaseController):
    """Controller for shopping cart operations"""
    
    def __init__(self):
        super().__init__()
        self.cart_service = CartService()
        self.serializer = ResponseSerializer()
    
    def serialize_cart_item(self, cart_item: CartItem) -> Dict[str, Any]:
        """Serialize cart item for API response"""
        return {
            'id': cart_item.id,
            'session_id': cart_item.session_id,
            'customer_id': cart_item.customer_id,
            'product_id': cart_item.product_id,
            'product_name': cart_item.product_name,
            'product_price': float(cart_item.product_price),
            'quantity': cart_item.quantity,
            'subtotal': float(cart_item.subtotal),
            'created_at': cart_item.created_at.isoformat() if cart_item.created_at else None,
            'updated_at': cart_item.updated_at.isoformat() if cart_item.updated_at else None
        }
    
    def get_user_identifier(self) -> Dict[str, Optional[int]]:
        """Get user identifier (customer_id or session_id)"""
        try:
            verify_jwt_in_request(optional=True)
            customer_id = get_jwt_identity()
            return {
                'customer_id': customer_id,
                'session_id': request.headers.get('X-Session-ID') if not customer_id else None
            }
        except:
            return {
                'customer_id': None,
                'session_id': request.headers.get('X-Session-ID')
            }


# Initialize controller
controller = CartController()


@cart_bp.route('', methods=['GET'])
@handle_api_errors
def get_cart():
    """Get shopping cart contents"""
    try:
        user_id = controller.get_user_identifier()
        
        if not user_id['customer_id'] and not user_id['session_id']:
            return jsonify({
                'success': False,
                'message': 'Session ID required for guest users'
            }), 400
        
        # Get cart items
        cart_items = controller.cart_service.get_cart_items(**user_id)
        
        # Calculate totals
        subtotal = sum(item.subtotal for item in cart_items)
        item_count = sum(item.quantity for item in cart_items)
        
        return jsonify({
            'success': True,
            'data': {
                'items': [controller.serialize_cart_item(item) for item in cart_items],
                'subtotal': float(subtotal),
                'item_count': item_count,
                'customer_id': user_id['customer_id'],
                'session_id': user_id['session_id']
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting cart: {e}")
        return jsonify({
            'success': False,
            'message': 'Error retrieving cart'
        }), 500


@cart_bp.route('/items', methods=['POST'])
@handle_api_errors
def add_to_cart():
    """Add item to shopping cart"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['product_id', 'quantity']
        validate_required_fields(data, required_fields)
        
        user_id = controller.get_user_identifier()
        
        if not user_id['customer_id'] and not user_id['session_id']:
            return jsonify({
                'success': False,
                'message': 'Session ID required for guest users'
            }), 400
        
        # Add item to cart
        cart_item = controller.cart_service.add_to_cart(
            product_id=data['product_id'],
            quantity=data['quantity'],
            **user_id
        )
        
        if cart_item:
            return jsonify({
                'success': True,
                'message': 'Item added to cart',
                'data': controller.serialize_cart_item(cart_item)
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to add item to cart'
            }), 400
            
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'errors': e.errors if hasattr(e, 'errors') else []
        }), 400
    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        return jsonify({
            'success': False,
            'message': 'Error adding item to cart'
        }), 500


@cart_bp.route('/items/<int:item_id>', methods=['PUT'])
@handle_api_errors
def update_cart_item(item_id: int):
    """Update cart item quantity"""
    try:
        data = request.get_json()
        
        if 'quantity' not in data:
            return jsonify({
                'success': False,
                'message': 'Quantity is required'
            }), 400
        
        user_id = controller.get_user_identifier()
        
        # Update cart item
        cart_item = controller.cart_service.update_cart_item(
            item_id=item_id,
            quantity=data['quantity'],
            **user_id
        )
        
        if cart_item:
            return jsonify({
                'success': True,
                'message': 'Cart item updated',
                'data': controller.serialize_cart_item(cart_item)
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Cart item not found or update failed'
            }), 404
            
    except Exception as e:
        logger.error(f"Error updating cart item: {e}")
        return jsonify({
            'success': False,
            'message': 'Error updating cart item'
        }), 500


@cart_bp.route('/items/<int:item_id>', methods=['DELETE'])
@handle_api_errors
def remove_from_cart(item_id: int):
    """Remove item from shopping cart"""
    try:
        user_id = controller.get_user_identifier()
        
        # Remove item from cart
        success = controller.cart_service.remove_from_cart(
            item_id=item_id,
            **user_id
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Item removed from cart'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Cart item not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error removing from cart: {e}")
        return jsonify({
            'success': False,
            'message': 'Error removing item from cart'
        }), 500


@cart_bp.route('/clear', methods=['DELETE'])
@handle_api_errors  
def clear_cart():
    """Clear all items from shopping cart"""
    try:
        user_id = controller.get_user_identifier()
        
        if not user_id['customer_id'] and not user_id['session_id']:
            return jsonify({
                'success': False,
                'message': 'Session ID required for guest users'
            }), 400
        
        # Clear cart
        success = controller.cart_service.clear_cart(**user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Cart cleared'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Error clearing cart'
            }), 500
            
    except Exception as e:
        logger.error(f"Error clearing cart: {e}")
        return jsonify({
            'success': False,
            'message': 'Error clearing cart'
        }), 500


@cart_bp.route('/merge', methods=['POST'])
@handle_api_errors
@jwt_required()
def merge_carts():
    """Merge guest cart with customer cart after login"""
    try:
        data = request.get_json()
        customer_id = get_jwt_identity()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({
                'success': False,
                'message': 'Session ID is required for cart merge'
            }), 400
        
        # Merge carts
        success = controller.cart_service.merge_guest_cart_to_customer(
            session_id=session_id,
            customer_id=customer_id
        )
        
        if success:
            # Get merged cart
            cart_items = controller.cart_service.get_cart_items(customer_id=customer_id)
            subtotal = sum(item.subtotal for item in cart_items)
            item_count = sum(item.quantity for item in cart_items)
            
            return jsonify({
                'success': True,
                'message': 'Carts merged successfully',
                'data': {
                    'items': [controller.serialize_cart_item(item) for item in cart_items],
                    'subtotal': float(subtotal),
                    'item_count': item_count
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Error merging carts'
            }), 500
            
    except Exception as e:
        logger.error(f"Error merging carts: {e}")
        return jsonify({
            'success': False,
            'message': 'Error merging carts'
        }), 500


@cart_bp.route('/count', methods=['GET'])
@handle_api_errors
def get_cart_count():
    """Get cart item count (for cart badge)"""
    try:
        user_id = controller.get_user_identifier()
        
        if not user_id['customer_id'] and not user_id['session_id']:
            return jsonify({
                'success': True,
                'data': {'count': 0}
            })
        
        # Get cart count
        count = controller.cart_service.get_cart_item_count(**user_id)
        
        return jsonify({
            'success': True,
            'data': {'count': count}
        })
        
    except Exception as e:
        logger.error(f"Error getting cart count: {e}")
        return jsonify({
            'success': False,
            'message': 'Error retrieving cart count'
        }), 500


# Health check endpoint
@cart_bp.route('/health', methods=['GET'])
def cart_health():
    """Cart service health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'cart-service',
        'endpoints': [
            'GET /api/cart',
            'POST /api/cart/items', 
            'PUT /api/cart/items/<id>',
            'DELETE /api/cart/items/<id>',
            'DELETE /api/cart/clear',
            'POST /api/cart/merge',
            'GET /api/cart/count'
        ]
    })