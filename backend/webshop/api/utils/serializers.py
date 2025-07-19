#!/usr/bin/env python3
"""
API Serializers - Convert model objects to JSON-serializable dictionaries
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from abc import ABC, abstractmethod


class BaseSerializer(ABC):
    """Base serializer class"""
    
    @abstractmethod
    def serialize(self, obj: Any) -> Dict[str, Any]:
        """Serialize object to dictionary"""
        pass
    
    def serialize_many(self, objects: List[Any]) -> List[Dict[str, Any]]:
        """Serialize list of objects"""
        return [self.serialize(obj) for obj in objects]
    
    @staticmethod
    def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
        """Serialize datetime to ISO format string"""
        return dt.isoformat() if dt else None


class ProductSerializer(BaseSerializer):
    """Serializer for Product model"""
    
    def serialize(self, product) -> Dict[str, Any]:
        """Serialize product object"""
        return {
            'id': product.id,
            'name': product.name,
            'title': product.title,
            'slug': product.slug,
            'short_description': product.short_description,
            'full_description': product.full_description,
            'price': float(product.price) if product.price else None,
            'price_type': product.price_type,
            'currency': product.currency,
            'status': product.status,
            'category_id': product.category_id,
            'category': self._serialize_category(product.category) if hasattr(product, 'category') and product.category else None,
            'featured': product.featured,
            'view_count': product.view_count or 0,
            'download_count': product.download_count or 0,
            'thumbs_up_count': product.thumbs_up_count or 0,
            'keywords': product.keywords,
            'meta_title': product.meta_title,
            'meta_description': product.meta_description,
            'image_url': product.image_url,
            'gallery_images': product.gallery_images.split(',') if product.gallery_images else [],
            'created_at': self.serialize_datetime(product.created_at),
            'updated_at': self.serialize_datetime(product.updated_at)
        }
    
    def _serialize_category(self, category) -> Dict[str, Any]:
        """Serialize related category"""
        return {
            'id': category.id,
            'name': category.name,
            'slug': category.slug
        }


class ProductCategorySerializer(BaseSerializer):
    """Serializer for ProductCategory model"""
    
    def serialize(self, category) -> Dict[str, Any]:
        """Serialize category object"""
        return {
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'description': category.description,
            'parent_id': category.parent_id,
            'sort_order': category.sort_order or 0,
            'is_active': category.is_active,
            'created_at': self.serialize_datetime(category.created_at),
            'updated_at': self.serialize_datetime(category.updated_at)
        }


class CustomerSerializer(BaseSerializer):
    """Serializer for Customer model"""
    
    def serialize(self, customer, include_sensitive: bool = False) -> Dict[str, Any]:
        """Serialize customer object"""
        data = {
            'id': customer.id,
            'email': customer.email,
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'phone': customer.phone,
            'company': customer.company,
            'website': customer.website,
            'email_verified': customer.email_verified,
            'is_active': customer.is_active,
            'created_at': self.serialize_datetime(customer.created_at),
            'updated_at': self.serialize_datetime(customer.updated_at)
        }
        
        # Include sensitive data only if explicitly requested (admin views)
        if include_sensitive:
            data.update({
                'login_count': customer.login_count or 0,
                'last_login_at': self.serialize_datetime(customer.last_login_at),
                'last_login_ip': customer.last_login_ip,
                'registration_ip': customer.registration_ip,
                'referral_source': customer.referral_source
            })
        
        return data


class OrderSerializer(BaseSerializer):
    """Serializer for Order model"""
    
    def serialize(self, order) -> Dict[str, Any]:
        """Serialize order object"""
        return {
            'id': order.id,
            'order_number': order.order_number,
            'customer_id': order.customer_id,
            'status': order.status,
            'subtotal': float(order.subtotal) if order.subtotal else 0.0,
            'tax_amount': float(order.tax_amount) if order.tax_amount else 0.0,
            'total_amount': float(order.total_amount) if order.total_amount else 0.0,
            'currency': order.currency or 'USD',
            'billing_first_name': order.billing_first_name,
            'billing_last_name': order.billing_last_name,
            'billing_email': order.billing_email,
            'billing_phone': order.billing_phone,
            'billing_company': order.billing_company,
            'billing_address': order.billing_address,
            'billing_city': order.billing_city,
            'billing_state': order.billing_state,
            'billing_country': order.billing_country,
            'billing_postal_code': order.billing_postal_code,
            'customer_notes': order.customer_notes,
            'admin_notes': order.admin_notes,
            'terms_accepted': order.terms_accepted,
            'terms_accepted_at': self.serialize_datetime(order.terms_accepted_at),
            'created_at': self.serialize_datetime(order.created_at),
            'updated_at': self.serialize_datetime(order.updated_at)
        }


class OrderItemSerializer(BaseSerializer):
    """Serializer for OrderItem model"""
    
    def serialize(self, item) -> Dict[str, Any]:
        """Serialize order item object"""
        return {
            'id': item.id,
            'order_id': item.order_id,
            'product_id': item.product_id,
            'product_name': item.product_name,
            'product_title': item.product_title,
            'product_price': float(item.product_price) if item.product_price else 0.0,
            'quantity': item.quantity or 1,
            'total_price': float(item.total_price) if item.total_price else 0.0,
            'download_url': item.download_url,
            'download_expires_at': self.serialize_datetime(item.download_expires_at),
            'download_count': item.download_count or 0,
            'max_downloads': item.max_downloads,
            'created_at': self.serialize_datetime(item.created_at)
        }


class PaymentSerializer(BaseSerializer):
    """Serializer for Payment model"""
    
    def serialize(self, payment) -> Dict[str, Any]:
        """Serialize payment object"""
        return {
            'id': payment.id,
            'order_id': payment.order_id,
            'processor': payment.processor,
            'transaction_id': payment.transaction_id,
            'amount': float(payment.amount) if payment.amount else 0.0,
            'currency': payment.currency or 'USD',
            'status': payment.status,
            'processor_response': payment.processor_response,
            'failure_reason': payment.failure_reason,
            'processed_at': self.serialize_datetime(payment.processed_at),
            'created_at': self.serialize_datetime(payment.created_at)
        }


class AdminUserSerializer(BaseSerializer):
    """Serializer for AdminUser model"""
    
    def serialize(self, admin_user, include_sensitive: bool = False) -> Dict[str, Any]:
        """Serialize admin user object"""
        data = {
            'id': admin_user.id,
            'email': admin_user.email,
            'first_name': admin_user.first_name,
            'last_name': admin_user.last_name,
            'role': admin_user.role,
            'is_active': admin_user.is_active,
            'created_at': self.serialize_datetime(admin_user.created_at),
            'updated_at': self.serialize_datetime(admin_user.updated_at)
        }
        
        # Include sensitive data only if explicitly requested
        if include_sensitive:
            data.update({
                'login_count': admin_user.login_count or 0,
                'last_login_at': self.serialize_datetime(admin_user.last_login_at),
                'last_login_ip': admin_user.last_login_ip,
                'password_changed_at': self.serialize_datetime(admin_user.password_changed_at),
                'password_expires_at': self.serialize_datetime(admin_user.password_expires_at)
            })
        
        return data


class SupportRequestSerializer(BaseSerializer):
    """Serializer for SupportRequest model"""
    
    def serialize(self, request) -> Dict[str, Any]:
        """Serialize support request object"""
        return {
            'id': request.id,
            'customer_id': request.customer_id,
            'subject': request.subject,
            'priority': request.priority,
            'status': request.status,
            'message': request.message,
            'customer_email': request.customer_email,
            'customer_name': request.customer_name,
            'admin_response': request.admin_response,
            'responded_by': request.responded_by,
            'responded_at': self.serialize_datetime(request.responded_at),
            'created_at': self.serialize_datetime(request.created_at),
            'updated_at': self.serialize_datetime(request.updated_at)
        }


class ProductInquirySerializer(BaseSerializer):
    """Serializer for ProductInquiry model"""
    
    def serialize(self, inquiry) -> Dict[str, Any]:
        """Serialize product inquiry object"""
        return {
            'id': inquiry.id,
            'product_id': inquiry.product_id,
            'customer_id': inquiry.customer_id,
            'customer_email': inquiry.customer_email,
            'customer_name': inquiry.customer_name,
            'question': inquiry.question,
            'admin_response': inquiry.admin_response,
            'status': inquiry.status,
            'responded_at': self.serialize_datetime(inquiry.responded_at),
            'created_at': self.serialize_datetime(inquiry.created_at)
        }