#!/usr/bin/env python3
"""
Webshop Services Package - Business logic for webshop functionality

Contains all webshop-related business logic services:
- Base service functionality
- Product management
- Order processing  
- Customer management
- Admin operations
"""

# Base service from core functionality
from .base_service import BaseService

# Domain-specific services
from .product_service import ProductService, ProductCategoryService, ProductReviewService, ProductInquiryService
from .order_service import OrderService, PaymentService, InstallationRequestService
from .customer_service import CustomerService, CustomerSessionService, SupportRequestService
from .admin_service import AdminUserService, AdminSessionService, ConfigSettingService, EmailTemplateService

__all__ = [
    'BaseService',
    
    # Product services
    'ProductService',
    'ProductCategoryService', 
    'ProductReviewService',
    'ProductInquiryService',
    
    # Order services
    'OrderService',
    'PaymentService',
    'InstallationRequestService',
    
    # Customer services
    'CustomerService',
    'CustomerSessionService',
    'SupportRequestService',
    
    # Admin services
    'AdminUserService',
    'AdminSessionService',
    'ConfigSettingService',
    'EmailTemplateService'
]