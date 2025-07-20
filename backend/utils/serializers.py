#!/usr/bin/env python3
"""
Serializers - Data serialization utilities for API responses
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from decimal import Decimal


class BaseSerializer:
    """Base serializer with common functionality"""
    
    def __init__(self, instance=None, data=None, many=False):
        self.instance = instance
        self.data = data
        self.many = many
    
    def to_dict(self) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Convert instance(s) to dictionary representation"""
        if self.many:
            return [self._serialize_instance(item) for item in self.instance]
        return self._serialize_instance(self.instance)
    
    def _serialize_instance(self, instance) -> Dict[str, Any]:
        """Override in subclasses to define serialization logic"""
        if hasattr(instance, 'to_dict'):
            return instance.to_dict()
        return {}
    
    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Convert various types to JSON-serializable values"""
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, Decimal):
            return float(value)
        elif hasattr(value, 'to_dict'):
            return value.to_dict()
        elif hasattr(value, '__dict__'):
            return {k: BaseSerializer._serialize_value(v) for k, v in value.__dict__.items() 
                   if not k.startswith('_')}
        return value


class ProductSerializer(BaseSerializer):
    """Serializer for Product model"""
    
    def _serialize_instance(self, product) -> Dict[str, Any]:
        if not product:
            return {}
        
        return {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': float(product.price) if product.price else 0.0,
            'category': product.category,
            'stock_quantity': product.stock_quantity,
            'image_urls': product.image_urls or [],
            'weight': product.weight,
            'dimensions': product.dimensions,
            'tags': product.tags or [],
            'is_active': product.is_active,
            'created_at': product.created_at.isoformat() if product.created_at else None,
            'updated_at': product.updated_at.isoformat() if product.updated_at else None
        }


class CustomerSerializer(BaseSerializer):
    """Serializer for Customer model"""
    
    def _serialize_instance(self, customer) -> Dict[str, Any]:
        if not customer:
            return {}
        
        data = {
            'id': customer.id,
            'email': customer.email,
            'firstName': customer.first_name,
            'lastName': customer.last_name,
            'phone': customer.phone,
            'is_active': customer.is_active,
            'is_admin': customer.is_admin,
            'email_verified': customer.email_verified,
            'created_at': customer.created_at.isoformat() if customer.created_at else None,
            'updated_at': customer.updated_at.isoformat() if customer.updated_at else None,
            'last_login': customer.last_login.isoformat() if customer.last_login else None
        }
        
        # Include address if available
        if hasattr(customer, 'address') and customer.address:
            data['address'] = {
                'street': customer.address.get('street'),
                'city': customer.address.get('city'),
                'state': customer.address.get('state'),
                'zipCode': customer.address.get('zip_code'),
                'country': customer.address.get('country', 'US')
            }
        
        return data


class OrderSerializer(BaseSerializer):
    """Serializer for Order model"""
    
    def _serialize_instance(self, order) -> Dict[str, Any]:
        if not order:
            return {}
        
        data = {
            'id': order.id,
            'customer_id': order.customer_id,
            'status': order.status,
            'total_amount': float(order.total_amount) if order.total_amount else 0.0,
            'subtotal': float(order.subtotal) if order.subtotal else 0.0,
            'tax_amount': float(order.tax_amount) if order.tax_amount else 0.0,
            'shipping_cost': float(order.shipping_cost) if order.shipping_cost else 0.0,
            'payment_status': order.payment_status,
            'payment_method': order.payment_method,
            'tracking_number': order.tracking_number,
            'notes': order.notes,
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'updated_at': order.updated_at.isoformat() if order.updated_at else None,
            'shipped_at': order.shipped_at.isoformat() if order.shipped_at else None,
            'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None
        }
        
        # Include shipping address
        if order.shipping_address:
            data['shipping_address'] = order.shipping_address
        
        # Include billing address
        if order.billing_address:
            data['billing_address'] = order.billing_address
        
        # Include order items if available
        if hasattr(order, 'items') and order.items:
            data['items'] = [OrderItemSerializer()._serialize_instance(item) for item in order.items]
        
        return data


class OrderItemSerializer(BaseSerializer):
    """Serializer for OrderItem model"""
    
    def _serialize_instance(self, item) -> Dict[str, Any]:
        if not item:
            return {}
        
        return {
            'id': item.id,
            'order_id': item.order_id,
            'product_id': item.product_id,
            'product_name': item.product_name,
            'unit_price': float(item.unit_price) if item.unit_price else 0.0,
            'quantity': item.quantity,
            'subtotal': float(item.subtotal) if item.subtotal else 0.0,
            'created_at': item.created_at.isoformat() if item.created_at else None
        }


class CartItemSerializer(BaseSerializer):
    """Serializer for CartItem model"""
    
    def _serialize_instance(self, item) -> Dict[str, Any]:
        if not item:
            return {}
        
        return {
            'id': item.id,
            'customer_id': item.customer_id,
            'session_id': item.session_id,
            'product_id': item.product_id,
            'product_name': item.product_name,
            'product_price': float(item.product_price) if item.product_price else 0.0,
            'quantity': item.quantity,
            'subtotal': float(item.subtotal) if item.subtotal else 0.0,
            'notes': item.notes,
            'created_at': item.created_at.isoformat() if item.created_at else None,
            'updated_at': item.updated_at.isoformat() if item.updated_at else None
        }


class AdminUserSerializer(BaseSerializer):
    """Serializer for AdminUser model"""
    
    def _serialize_instance(self, admin) -> Dict[str, Any]:
        if not admin:
            return {}
        
        return {
            'id': admin.id,
            'username': admin.username,
            'email': admin.email,
            'first_name': admin.first_name,
            'last_name': admin.last_name,
            'role': admin.role,
            'is_active': admin.is_active,
            'is_superuser': admin.is_superuser,
            'permissions': admin.permissions or [],
            'last_login': admin.last_login.isoformat() if admin.last_login else None,
            'created_at': admin.created_at.isoformat() if admin.created_at else None,
            'updated_at': admin.updated_at.isoformat() if admin.updated_at else None
        }


class PaymentSerializer(BaseSerializer):
    """Serializer for Payment model"""
    
    def _serialize_instance(self, payment) -> Dict[str, Any]:
        if not payment:
            return {}
        
        return {
            'id': payment.id,
            'order_id': payment.order_id,
            'payment_method': payment.payment_method,
            'amount': float(payment.amount) if payment.amount else 0.0,
            'currency': payment.currency,
            'status': payment.status,
            'transaction_id': payment.transaction_id,
            'gateway_response': payment.gateway_response,
            'created_at': payment.created_at.isoformat() if payment.created_at else None,
            'processed_at': payment.processed_at.isoformat() if payment.processed_at else None
        }


class CustomerSessionSerializer(BaseSerializer):
    """Serializer for CustomerSession model"""
    
    def _serialize_instance(self, session) -> Dict[str, Any]:
        if not session:
            return {}
        
        return {
            'id': session.id,
            'customer_id': session.customer_id,
            'session_token': session.session_token,  # Be careful with sensitive data
            'ip_address': session.ip_address,
            'user_agent': session.user_agent,
            'is_active': session.is_active,
            'created_at': session.created_at.isoformat() if session.created_at else None,
            'expires_at': session.expires_at.isoformat() if session.expires_at else None,
            'last_activity': session.last_activity.isoformat() if session.last_activity else None
        }


class PaginatedSerializer:
    """Wrapper for paginated responses"""
    
    def __init__(self, items: List[Any], serializer_class: BaseSerializer, 
                 page: int, per_page: int, total: int):
        self.items = items
        self.serializer_class = serializer_class
        self.page = page
        self.per_page = per_page
        self.total = total
    
    def to_dict(self) -> Dict[str, Any]:
        serializer = self.serializer_class(self.items, many=True)
        return {
            'data': serializer.to_dict(),
            'pagination': {
                'page': self.page,
                'per_page': self.per_page,
                'total': self.total,
                'pages': (self.total + self.per_page - 1) // self.per_page,
                'has_next': self.page * self.per_page < self.total,
                'has_prev': self.page > 1
            }
        }


# Utility functions for common serialization patterns
def serialize_model(instance, serializer_class: BaseSerializer = None) -> Dict[str, Any]:
    """Serialize a single model instance"""
    if serializer_class:
        return serializer_class(instance).to_dict()
    return BaseSerializer(instance).to_dict()


def serialize_models(instances: List[Any], serializer_class: BaseSerializer = None) -> List[Dict[str, Any]]:
    """Serialize a list of model instances"""
    if serializer_class:
        return serializer_class(instances, many=True).to_dict()
    return BaseSerializer(instances, many=True).to_dict()


def paginated_response(items: List[Any], serializer_class: BaseSerializer,
                      page: int, per_page: int, total: int) -> Dict[str, Any]:
    """Create a paginated response"""
    return PaginatedSerializer(items, serializer_class, page, per_page, total).to_dict()


# Export commonly used serializers
__all__ = [
    'BaseSerializer',
    'ProductSerializer',
    'CustomerSerializer', 
    'OrderSerializer',
    'OrderItemSerializer',
    'CartItemSerializer',
    'AdminUserSerializer',
    'PaymentSerializer',
    'CustomerSessionSerializer',
    'PaginatedSerializer',
    'serialize_model',
    'serialize_models',
    'paginated_response'
]