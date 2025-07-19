#!/usr/bin/env python3
"""
Order Models - Database models for order management and payment processing
Handles orders, order items, payments, and installation service requests
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from typing import Dict, Any, List, Optional
import json
from enum import Enum
from datetime import datetime

from core.orm.base_model import BaseModel


class OrderStatus(Enum):
    """Enumeration for order status"""
    PENDING = "pending"           # Order created, payment pending
    PAID = "paid"                # Payment successful
    PROCESSING = "processing"     # Order being processed
    COMPLETED = "completed"       # Order completed, files delivered
    CANCELLED = "cancelled"       # Order cancelled
    REFUNDED = "refunded"        # Order refunded


class PaymentStatus(Enum):
    """Enumeration for payment status"""
    PENDING = "pending"           # Payment initiated
    SUCCESS = "success"           # Payment successful
    FAILED = "failed"            # Payment failed
    CANCELLED = "cancelled"       # Payment cancelled
    REFUNDED = "refunded"        # Payment refunded


class PaymentProcessor(Enum):
    """Enumeration for payment processors"""
    STRIPE = "stripe"
    PAYPAL = "paypal"
    MANUAL = "manual"             # Manual/offline payment


class Order(BaseModel):
    """Customer order model"""
    
    __tablename__ = 'orders'
    
    # Customer and order identification
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False, index=True)
    order_number = Column(String(50), nullable=False, unique=True, index=True)
    
    # Order totals
    subtotal = Column(Float, nullable=False, default=0.0)
    tax_amount = Column(Float, nullable=False, default=0.0)
    total_amount = Column(Float, nullable=False, default=0.0)
    currency = Column(String(3), nullable=False, default='USD')
    
    # Order status
    status = Column(String(20), nullable=False, default=OrderStatus.PENDING.value)
    
    # Customer information (snapshot at time of order)
    billing_first_name = Column(String(100), nullable=False)
    billing_last_name = Column(String(100), nullable=False)
    billing_email = Column(String(255), nullable=False)
    billing_phone = Column(String(20))
    billing_address_line1 = Column(String(255), nullable=False)
    billing_address_line2 = Column(String(255))
    billing_city = Column(String(100), nullable=False)
    billing_state = Column(String(100))
    billing_postal_code = Column(String(20), nullable=False)
    billing_country = Column(String(100), nullable=False)
    
    # Terms and conditions
    terms_accepted = Column(Boolean, nullable=False, default=False)
    terms_accepted_at = Column(DateTime)
    terms_ip_address = Column(String(45))
    
    # Order processing
    processed_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Notes and special instructions
    customer_notes = Column(Text)
    admin_notes = Column(Text)
    
    # Relationships
    customer = relationship("Customer", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    installation_requests = relationship("InstallationRequest", back_populates="order", cascade="all, delete-orphan")
    support_requests = relationship("SupportRequest", back_populates="order")
    
    def __init__(self, **kwargs):
        """Initialize order with automatic order number generation"""
        super().__init__()
        
        # Generate order number if not provided
        if 'order_number' not in kwargs:
            kwargs['order_number'] = self._generate_order_number()
        
        # Set default values
        if 'status' not in kwargs:
            kwargs['status'] = OrderStatus.PENDING.value
        if 'currency' not in kwargs:
            kwargs['currency'] = 'USD'
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def _generate_order_number(self) -> str:
        """Generate unique order number"""
        from datetime import datetime
        import random
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_part = random.randint(1000, 9999)
        return f"AG-{timestamp}-{random_part}"
    
    def add_item(self, product, quantity: int = 1, price: float = None):
        """Add item to order"""
        from .product_models import Product
        
        if not isinstance(product, Product):
            raise ValueError("Product must be a Product instance")
        
        # Use product price if not specified
        if price is None:
            price = product.price or 0.0
        
        # Check if item already exists
        existing_item = None
        for item in self.order_items:
            if item.product_id == product.id:
                existing_item = item
                break
        
        if existing_item:
            existing_item.quantity += quantity
            existing_item.total_price = existing_item.quantity * existing_item.unit_price
        else:
            order_item = OrderItem(
                order_id=self.id,
                product_id=product.id,
                product_name=product.name,
                unit_price=price,
                quantity=quantity,
                total_price=price * quantity
            )
            self.order_items.append(order_item)
        
        self._calculate_totals()
    
    def remove_item(self, product_id: int):
        """Remove item from order"""
        self.order_items = [item for item in self.order_items if item.product_id != product_id]
        self._calculate_totals()
    
    def _calculate_totals(self):
        """Calculate order totals"""
        self.subtotal = sum(item.total_price for item in self.order_items)
        # Tax calculation could be implemented here
        self.tax_amount = 0.0  # Simplified - no tax for now
        self.total_amount = self.subtotal + self.tax_amount
    
    def get_payment_status(self) -> str:
        """Get overall payment status for order"""
        if not self.payments:
            return PaymentStatus.PENDING.value
        
        successful_payments = [p for p in self.payments if p.status == PaymentStatus.SUCCESS.value]
        failed_payments = [p for p in self.payments if p.status == PaymentStatus.FAILED.value]
        
        if successful_payments:
            total_paid = sum(p.amount for p in successful_payments)
            if total_paid >= self.total_amount:
                return PaymentStatus.SUCCESS.value
        
        if failed_payments:
            return PaymentStatus.FAILED.value
        
        return PaymentStatus.PENDING.value
    
    def mark_as_paid(self):
        """Mark order as paid and update status"""
        if self.get_payment_status() == PaymentStatus.SUCCESS.value:
            self.status = OrderStatus.PAID.value
    
    def complete_order(self):
        """Mark order as completed"""
        self.status = OrderStatus.COMPLETED.value
        self.completed_at = datetime.utcnow()
    
    def cancel_order(self, reason: str = None):
        """Cancel order"""
        self.status = OrderStatus.CANCELLED.value
        if reason:
            self.admin_notes = f"Cancelled: {reason}"
    
    @property
    def billing_full_name(self) -> str:
        """Get full billing name"""
        return f"{self.billing_first_name} {self.billing_last_name}".strip()
    
    @property
    def billing_address(self) -> str:
        """Get formatted billing address"""
        address_parts = [self.billing_address_line1]
        if self.billing_address_line2:
            address_parts.append(self.billing_address_line2)
        address_parts.extend([
            self.billing_city,
            self.billing_state,
            self.billing_postal_code,
            self.billing_country
        ])
        return ', '.join(filter(None, address_parts))
    
    def validate(self) -> Dict[str, List[str]]:
        """Validate order data"""
        errors = super().validate()
        
        # Validate required billing information
        required_billing_fields = [
            'billing_first_name', 'billing_last_name', 'billing_email',
            'billing_address_line1', 'billing_city', 'billing_postal_code', 'billing_country'
        ]
        
        for field in required_billing_fields:
            value = getattr(self, field)
            if not value or (isinstance(value, str) and not value.strip()):
                if field not in errors:
                    errors[field] = []
                errors[field].append(f"{field.replace('_', ' ').title()} is required")
        
        # Validate email format
        if self.billing_email and not self._is_valid_email(self.billing_email):
            if 'billing_email' not in errors:
                errors['billing_email'] = []
            errors['billing_email'].append("Invalid email format")
        
        # Validate terms acceptance
        if not self.terms_accepted:
            if 'terms_accepted' not in errors:
                errors['terms_accepted'] = []
            errors['terms_accepted'].append("Terms and conditions must be accepted")
        
        return errors
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None


class OrderItem(BaseModel):
    """Individual items within an order"""
    
    __tablename__ = 'order_items'
    
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    
    # Product snapshot at time of purchase
    product_name = Column(String(200), nullable=False)
    product_description = Column(Text)
    
    # Pricing
    unit_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    total_price = Column(Float, nullable=False)
    
    # Download information
    download_link = Column(String(500))
    download_expires_at = Column(DateTime)
    download_count = Column(Integer, default=0)
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")
    
    def __init__(self, **kwargs):
        super().__init__()
        
        # Calculate total price if not provided
        if 'total_price' not in kwargs and 'unit_price' in kwargs and 'quantity' in kwargs:
            kwargs['total_price'] = kwargs['unit_price'] * kwargs['quantity']
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def generate_download_link(self, expires_hours: int = 48) -> str:
        """Generate secure download link with expiration"""
        import secrets
        from datetime import timedelta
        
        token = secrets.token_urlsafe(32)
        self.download_link = f"/download/{token}"
        self.download_expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        return self.download_link
    
    def is_download_valid(self) -> bool:
        """Check if download link is still valid"""
        return (
            self.download_link and
            self.download_expires_at and
            datetime.utcnow() < self.download_expires_at
        )
    
    def record_download(self):
        """Record a download attempt"""
        self.download_count = (self.download_count or 0) + 1


class Payment(BaseModel):
    """Payment records for orders"""
    
    __tablename__ = 'payments'
    
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False, index=True)
    
    # Payment details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default='USD')
    payment_processor = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default=PaymentStatus.PENDING.value)
    
    # Transaction information
    transaction_id = Column(String(255), index=True)  # External transaction ID
    processor_transaction_id = Column(String(255))    # Processor-specific ID
    processor_fee = Column(Float, default=0.0)
    
    # Payment metadata
    payment_method = Column(String(50))  # card, paypal, etc.
    payment_details = Column(Text)       # JSON with additional details
    
    # Timestamps
    initiated_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    failed_at = Column(DateTime)
    
    # Error handling
    error_code = Column(String(50))
    error_message = Column(Text)
    
    # Relationships
    order = relationship("Order", back_populates="payments")
    
    def __init__(self, **kwargs):
        super().__init__()
        
        if 'status' not in kwargs:
            kwargs['status'] = PaymentStatus.PENDING.value
        if 'currency' not in kwargs:
            kwargs['currency'] = 'USD'
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def mark_successful(self, transaction_id: str = None, processor_fee: float = 0.0):
        """Mark payment as successful"""
        self.status = PaymentStatus.SUCCESS.value
        self.completed_at = datetime.utcnow()
        if transaction_id:
            self.processor_transaction_id = transaction_id
        self.processor_fee = processor_fee
    
    def mark_failed(self, error_code: str = None, error_message: str = None):
        """Mark payment as failed"""
        self.status = PaymentStatus.FAILED.value
        self.failed_at = datetime.utcnow()
        if error_code:
            self.error_code = error_code
        if error_message:
            self.error_message = error_message
    
    def get_payment_details(self) -> Dict[str, Any]:
        """Get payment details as dictionary"""
        if self.payment_details:
            try:
                return json.loads(self.payment_details)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_payment_details(self, details: Dict[str, Any]):
        """Set payment details from dictionary"""
        self.payment_details = json.dumps(details)


class InstallationRequest(BaseModel):
    """Installation service requests from customers"""
    
    __tablename__ = 'installation_requests'
    
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False, index=True)
    
    # Installation details
    odoo_version = Column(String(20), nullable=False)
    installation_period = Column(DateTime, nullable=False)
    comments = Column(Text)
    
    # Technical contact information
    tech_contact_name = Column(String(200), nullable=False)
    tech_contact_email = Column(String(255), nullable=False)
    tech_contact_phone = Column(String(20))
    
    # Request status
    status = Column(String(20), default='pending')  # pending, quoted, scheduled, completed, cancelled
    quote_amount = Column(Float)
    quote_sent_at = Column(DateTime)
    
    # Installation tracking
    scheduled_at = Column(DateTime)
    completed_at = Column(DateTime)
    technician_notes = Column(Text)
    
    # Relationships
    order = relationship("Order", back_populates="installation_requests")
    
    def validate(self) -> Dict[str, List[str]]:
        """Validate installation request data"""
        errors = super().validate()
        
        # Validate Odoo version
        valid_versions = ['13.0', '14.0', '15.0', '16.0', '17.0', '18.0']
        if self.odoo_version and self.odoo_version not in valid_versions:
            if 'odoo_version' not in errors:
                errors['odoo_version'] = []
            errors['odoo_version'].append(f"Invalid Odoo version. Must be one of: {', '.join(valid_versions)}")
        
        # Validate email format
        if self.tech_contact_email and not self._is_valid_email(self.tech_contact_email):
            if 'tech_contact_email' not in errors:
                errors['tech_contact_email'] = []
            errors['tech_contact_email'].append("Invalid email format")
        
        # Validate installation period (must be in future)
        if self.installation_period and self.installation_period <= datetime.utcnow():
            if 'installation_period' not in errors:
                errors['installation_period'] = []
            errors['installation_period'].append("Installation period must be in the future")
        
        return errors
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def send_quote(self, amount: float):
        """Mark quote as sent"""
        self.status = 'quoted'
        self.quote_amount = amount
        self.quote_sent_at = datetime.utcnow()
    
    def schedule_installation(self, scheduled_date: datetime):
        """Schedule the installation"""
        self.status = 'scheduled'
        self.scheduled_at = scheduled_date
    
    def complete_installation(self, notes: str = None):
        """Mark installation as completed"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        if notes:
            self.technician_notes = notes


# Import references for relationships
from .customer_models import Customer, SupportRequest
from .product_models import Product