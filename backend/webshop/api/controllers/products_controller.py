#!/usr/bin/env python3
"""
Products Controller - REST API endpoints for product management
Handles products, categories, reviews, and inquiries
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import logging
from typing import Dict, Any

from .base_controller import (
    BaseController, require_auth, require_admin, 
    handle_service_errors, rate_limit
)
from ...services.product_service import (
    ProductService, ProductCategoryService, 
    ProductReviewService, ProductInquiryService
)
from ..utils.serializers import ProductSerializer, ProductCategorySerializer

logger = logging.getLogger(__name__)

# Create blueprint
products_bp = Blueprint('products', __name__)


class ProductsController(BaseController):
    """Controller for Product-related endpoints"""
    
    def __init__(self):
        self.product_service = ProductService()
        self.category_service = ProductCategoryService()
        self.review_service = ProductReviewService()
        self.inquiry_service = ProductInquiryService()
        self.serializer = ProductSerializer()
        self.category_serializer = ProductCategorySerializer()


# Initialize controller
controller = ProductsController()


# Product CRUD Endpoints

@products_bp.route('/', methods=['GET'])
@handle_service_errors
@rate_limit("100/hour")
def get_products():
    """
    Get paginated list of products with filtering and search
    
    Query Parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20, max: 100)
        - search: Search term
        - category: Category ID filter
        - price_type: Price type filter (fixed, free, quote)
        - min_price: Minimum price filter
        - max_price: Maximum price filter
        - status: Product status (active, inactive, draft)
    """
    page, per_page = controller.get_pagination_params()
    search_params = controller.get_search_params()
    
    # Extract product-specific filters
    category_id = request.args.get('category', type=int)
    price_type = request.args.get('price_type')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    status = request.args.get('status', 'active')
    
    # For public API, only show active products unless admin
    if not _is_admin_request():
        status = 'active'
    
    if search_params['search']:
        products = controller.product_service.search_products(
            search_term=search_params['search'],
            category_id=category_id,
            price_type=price_type,
            min_price=min_price,
            max_price=max_price,
            limit=per_page,
            offset=(page - 1) * per_page
        )
        total = len(products)  # Simplified - should implement count query
    else:
        if status == 'active':
            products = controller.product_service.get_active_products(
                category_id=category_id,
                limit=per_page,
                offset=(page - 1) * per_page
            )
        else:
            # Admin can see all products
            filters = {'status': status} if status != 'all' else {}
            if category_id:
                filters['category_id'] = category_id
            products = controller.product_service.get_all(
                filters=filters,
                limit=per_page,
                offset=(page - 1) * per_page
            )
        total = len(products)  # Simplified
    
    # Serialize products
    serialized_products = [controller.serializer.serialize(p) for p in products]
    
    return controller.paginated_response(
        items=serialized_products,
        total=total,
        page=page,
        per_page=per_page,
        message=f"Found {len(products)} products"
    )


@products_bp.route('/<int:product_id>', methods=['GET'])
@handle_service_errors
@rate_limit("200/hour")
def get_product(product_id: int):
    """Get single product by ID"""
    product = controller.product_service.get_by_id(product_id)
    
    if not product:
        return controller.error_response("Product not found", 404)
    
    # Check if product is accessible
    if not _is_admin_request() and product.status != 'active':
        return controller.error_response("Product not found", 404)
    
    return controller.success_response(
        data=controller.serializer.serialize(product),
        message="Product retrieved successfully"
    )


@products_bp.route('/slug/<string:slug>', methods=['GET'])
@handle_service_errors
@rate_limit("200/hour")
def get_product_by_slug(slug: str):
    """Get product by URL slug (increments view count)"""
    product = controller.product_service.get_by_slug(slug)
    
    if not product:
        return controller.error_response("Product not found", 404)
    
    # Check if product is accessible
    if not _is_admin_request() and product.status != 'active':
        return controller.error_response("Product not found", 404)
    
    return controller.success_response(
        data=controller.serializer.serialize(product),
        message="Product retrieved successfully"
    )


@products_bp.route('/', methods=['POST'])
@require_admin
@handle_service_errors
@rate_limit("50/hour")
def create_product():
    """Create new product (admin only)"""
    data = controller.validate_json_request(
        required_fields=['name', 'title', 'price_type']
    )
    
    product = controller.product_service.create(data)
    
    return controller.success_response(
        data=controller.serializer.serialize(product),
        message="Product created successfully",
        status_code=201
    )


@products_bp.route('/<int:product_id>', methods=['PUT'])
@require_admin
@handle_service_errors
@rate_limit("100/hour")
def update_product(product_id: int):
    """Update product (admin only)"""
    data = controller.validate_json_request()
    
    product = controller.product_service.update(product_id, data)
    
    if not product:
        return controller.error_response("Product not found", 404)
    
    return controller.success_response(
        data=controller.serializer.serialize(product),
        message="Product updated successfully"
    )


@products_bp.route('/<int:product_id>', methods=['DELETE'])
@require_admin
@handle_service_errors
@rate_limit("20/hour")
def delete_product(product_id: int):
    """Delete product (admin only)"""
    success = controller.product_service.delete(product_id)
    
    if not success:
        return controller.error_response("Product not found or cannot be deleted", 404)
    
    return controller.success_response(
        message="Product deleted successfully"
    )


# Product Actions

@products_bp.route('/<int:product_id>/publish', methods=['POST'])
@require_admin
@handle_service_errors
@rate_limit("50/hour")
def publish_product(product_id: int):
    """Publish product (change status to active)"""
    success = controller.product_service.publish_product(product_id)
    
    if not success:
        return controller.error_response("Failed to publish product", 400)
    
    return controller.success_response(
        message="Product published successfully"
    )


@products_bp.route('/<int:product_id>/unpublish', methods=['POST'])
@require_admin
@handle_service_errors
@rate_limit("50/hour")
def unpublish_product(product_id: int):
    """Unpublish product (change status to inactive)"""
    success = controller.product_service.unpublish_product(product_id)
    
    if not success:
        return controller.error_response("Failed to unpublish product", 400)
    
    return controller.success_response(
        message="Product unpublished successfully"
    )


@products_bp.route('/<int:product_id>/download', methods=['POST'])
@handle_service_errors
@rate_limit("20/hour")
def record_download(product_id: int):
    """Record product download"""
    success = controller.product_service.record_download(product_id)
    
    if not success:
        return controller.error_response("Failed to record download", 400)
    
    return controller.success_response(
        message="Download recorded successfully"
    )


@products_bp.route('/featured', methods=['GET'])
@handle_service_errors
@rate_limit("100/hour")
def get_featured_products():
    """Get featured products for homepage"""
    limit = request.args.get('limit', 6, type=int)
    limit = min(limit, 20)  # Max 20 featured products
    
    products = controller.product_service.get_featured_products(limit)
    serialized_products = [controller.serializer.serialize(p) for p in products]
    
    return controller.success_response(
        data=serialized_products,
        message=f"Found {len(products)} featured products"
    )


@products_bp.route('/<int:product_id>/related', methods=['GET'])
@handle_service_errors
@rate_limit("100/hour")
def get_related_products(product_id: int):
    """Get products related to specified product"""
    product = controller.product_service.get_by_id(product_id)
    
    if not product:
        return controller.error_response("Product not found", 404)
    
    limit = request.args.get('limit', 4, type=int)
    limit = min(limit, 10)  # Max 10 related products
    
    related_products = controller.product_service.get_related_products(product, limit)
    serialized_products = [controller.serializer.serialize(p) for p in related_products]
    
    return controller.success_response(
        data=serialized_products,
        message=f"Found {len(related_products)} related products"
    )


# Product Categories

@products_bp.route('/categories', methods=['GET'])
@handle_service_errors
@rate_limit("100/hour")
def get_categories():
    """Get product categories"""
    tree = request.args.get('tree', 'false').lower() == 'true'
    
    if tree:
        categories = controller.category_service.get_category_tree()
        return controller.success_response(
            data=categories,
            message="Category tree retrieved successfully"
        )
    else:
        categories = controller.category_service.get_active_categories()
        serialized_categories = [controller.category_serializer.serialize(c) for c in categories]
        
        return controller.success_response(
            data=serialized_categories,
            message=f"Found {len(categories)} categories"
        )


@products_bp.route('/categories', methods=['POST'])
@require_admin
@handle_service_errors
@rate_limit("50/hour")
def create_category():
    """Create product category (admin only)"""
    data = controller.validate_json_request(
        required_fields=['name']
    )
    
    category = controller.category_service.create(data)
    
    return controller.success_response(
        data=controller.category_serializer.serialize(category),
        message="Category created successfully",
        status_code=201
    )


# Product Reviews (Thumbs Up System)

@products_bp.route('/<int:product_id>/thumbs-up', methods=['POST'])
@handle_service_errors
@rate_limit("10/hour")
def add_thumbs_up(product_id: int):
    """Add thumbs up review for product"""
    data = controller.validate_json_request(
        required_fields=['validation_answer']
    )
    
    customer_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
    customer_id = None
    
    # Get customer ID if authenticated
    try:
        verify_jwt_in_request(optional=True)
        customer_id = get_jwt_identity()
    except:
        pass
    
    success = controller.review_service.add_thumbs_up(
        product_id=product_id,
        validation_answer=data['validation_answer'],
        customer_ip=customer_ip,
        customer_id=customer_id
    )
    
    if not success:
        return controller.error_response("Failed to add thumbs up", 400)
    
    return controller.success_response(
        message="Thumbs up added successfully"
    )


@products_bp.route('/<int:product_id>/thumbs-up/count', methods=['GET'])
@handle_service_errors
@rate_limit("200/hour")
def get_thumbs_up_count(product_id: int):
    """Get thumbs up count for product"""
    count = controller.review_service.get_product_thumbs_up_count(product_id)
    
    return controller.success_response(
        data={'count': count},
        message="Thumbs up count retrieved successfully"
    )


# Product Inquiries

@products_bp.route('/<int:product_id>/inquiries', methods=['POST'])
@handle_service_errors
@rate_limit("5/hour")
def create_inquiry(product_id: int):
    """Create product inquiry"""
    data = controller.validate_json_request(
        required_fields=['customer_email', 'question']
    )
    
    customer_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
    customer_id = None
    
    # Get customer ID if authenticated
    try:
        verify_jwt_in_request(optional=True)
        customer_id = get_jwt_identity()
    except:
        pass
    
    inquiry = controller.inquiry_service.create_inquiry(
        product_id=product_id,
        customer_email=data['customer_email'],
        question=data['question'],
        customer_name=data.get('customer_name'),
        validation_answer=data.get('validation_answer'),
        customer_ip=customer_ip,
        customer_id=customer_id
    )
    
    if not inquiry:
        return controller.error_response("Failed to create inquiry", 400)
    
    return controller.success_response(
        message="Inquiry created successfully",
        status_code=201
    )


@products_bp.route('/<int:product_id>/inquiries', methods=['GET'])
@require_admin
@handle_service_errors
@rate_limit("100/hour")
def get_product_inquiries(product_id: int):
    """Get inquiries for product (admin only)"""
    status = request.args.get('status')
    inquiries = controller.inquiry_service.get_product_inquiries(product_id, status)
    
    # Serialize inquiries (would need inquiry serializer)
    serialized_inquiries = [inquiry.to_dict() for inquiry in inquiries]
    
    return controller.success_response(
        data=serialized_inquiries,
        message=f"Found {len(inquiries)} inquiries"
    )


# Statistics and Admin Endpoints

@products_bp.route('/stats', methods=['GET'])
@require_admin
@handle_service_errors
@rate_limit("20/hour")
def get_product_stats():
    """Get product statistics (admin only)"""
    stats = controller.product_service.get_product_stats()
    
    return controller.success_response(
        data=stats,
        message="Product statistics retrieved successfully"
    )


# Helper Functions

def _is_admin_request() -> bool:
    """Check if current request is from an admin user"""
    try:
        verify_jwt_in_request(optional=True)
        claims = get_jwt()
        return claims.get('is_admin', False) if claims else False
    except:
        return False