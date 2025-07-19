#!/usr/bin/env python3
"""
Payment Service - Handles payment processing with multiple providers
"""

import logging
from typing import Dict, Any, Optional
from decimal import Decimal
import os
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class PaymentResult:
    """Result of a payment processing operation"""
    
    def __init__(self, success: bool, transaction_id: str = None, 
                 error_message: str = None, raw_response: Dict = None):
        self.success = success
        self.transaction_id = transaction_id
        self.error_message = error_message
        self.raw_response = raw_response or {}


class BasePaymentProvider:
    """Base class for payment providers"""
    
    def __init__(self):
        self.enabled = False
    
    def process_payment(self, amount: Decimal, payment_method: Dict[str, Any], 
                       metadata: Dict[str, Any] = None) -> PaymentResult:
        """Process a payment"""
        raise NotImplementedError("Subclasses must implement process_payment")
    
    def refund_payment(self, transaction_id: str, amount: Decimal = None) -> PaymentResult:
        """Refund a payment"""
        raise NotImplementedError("Subclasses must implement refund_payment")
    
    def verify_webhook(self, payload: str, signature: str) -> bool:
        """Verify webhook signature"""
        raise NotImplementedError("Subclasses must implement verify_webhook")


class StripePaymentProvider(BasePaymentProvider):
    """Stripe payment provider"""
    
    def __init__(self):
        super().__init__()
        self.secret_key = os.getenv('STRIPE_SECRET_KEY')
        self.publishable_key = os.getenv('STRIPE_PUBLISHABLE_KEY')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        self.enabled = bool(self.secret_key)
        
        if self.enabled:
            try:
                import stripe
                self.stripe = stripe
                stripe.api_key = self.secret_key
            except ImportError:
                logger.error("Stripe library not installed. Install with: pip install stripe")
                self.enabled = False
    
    def process_payment(self, amount: Decimal, payment_method: Dict[str, Any], 
                       metadata: Dict[str, Any] = None) -> PaymentResult:
        """Process payment with Stripe"""
        if not self.enabled:
            return PaymentResult(
                success=False, 
                error_message="Stripe payment provider not configured"
            )
        
        try:
            # Convert amount to cents (Stripe uses smallest currency unit)
            amount_cents = int(amount * 100)
            
            # Create payment intent
            intent = self.stripe.PaymentIntent.create(
                amount=amount_cents,
                currency='usd',  # TODO: Support multiple currencies
                payment_method=payment_method.get('id'),
                confirmation_method='manual',
                confirm=True,
                metadata=metadata or {},
                return_url=os.getenv('STRIPE_RETURN_URL', 'http://localhost:3000/payment/return')
            )
            
            if intent.status == 'succeeded':
                return PaymentResult(
                    success=True,
                    transaction_id=intent.id,
                    raw_response=intent
                )
            elif intent.status == 'requires_action':
                # 3D Secure or other authentication required
                return PaymentResult(
                    success=False,
                    error_message="Additional authentication required",
                    raw_response=intent
                )
            else:
                return PaymentResult(
                    success=False,
                    error_message=f"Payment failed with status: {intent.status}",
                    raw_response=intent
                )
                
        except Exception as e:
            logger.error(f"Stripe payment processing error: {e}")
            return PaymentResult(
                success=False,
                error_message=str(e)
            )
    
    def refund_payment(self, transaction_id: str, amount: Decimal = None) -> PaymentResult:
        """Refund a Stripe payment"""
        if not self.enabled:
            return PaymentResult(
                success=False,
                error_message="Stripe payment provider not configured"
            )
        
        try:
            refund_data = {'payment_intent': transaction_id}
            if amount is not None:
                refund_data['amount'] = int(amount * 100)
            
            refund = self.stripe.Refund.create(**refund_data)
            
            return PaymentResult(
                success=True,
                transaction_id=refund.id,
                raw_response=refund
            )
            
        except Exception as e:
            logger.error(f"Stripe refund error: {e}")
            return PaymentResult(
                success=False,
                error_message=str(e)
            )
    
    def verify_webhook(self, payload: str, signature: str) -> bool:
        """Verify Stripe webhook signature"""
        if not self.enabled or not self.webhook_secret:
            return False
        
        try:
            event = self.stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return True
        except Exception as e:
            logger.error(f"Stripe webhook verification failed: {e}")
            return False


class PayPalPaymentProvider(BasePaymentProvider):
    """PayPal payment provider"""
    
    def __init__(self):
        super().__init__()
        self.client_id = os.getenv('PAYPAL_CLIENT_ID')
        self.client_secret = os.getenv('PAYPAL_CLIENT_SECRET')
        self.sandbox_mode = os.getenv('PAYPAL_SANDBOX', 'true').lower() == 'true'
        self.enabled = bool(self.client_id and self.client_secret)
        
        if self.enabled:
            try:
                import paypalrestsdk
                self.paypal = paypalrestsdk
                
                # Configure PayPal
                paypalrestsdk.configure({
                    'mode': 'sandbox' if self.sandbox_mode else 'live',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret
                })
                
            except ImportError:
                logger.error("PayPal library not installed. Install with: pip install paypalrestsdk")
                self.enabled = False
    
    def process_payment(self, amount: Decimal, payment_method: Dict[str, Any], 
                       metadata: Dict[str, Any] = None) -> PaymentResult:
        """Process payment with PayPal"""
        if not self.enabled:
            return PaymentResult(
                success=False,
                error_message="PayPal payment provider not configured"
            )
        
        try:
            payment = self.paypal.Payment({
                'intent': 'sale',
                'payer': {
                    'payment_method': 'paypal'
                },
                'redirect_urls': {
                    'return_url': os.getenv('PAYPAL_RETURN_URL', 'http://localhost:3000/payment/return'),
                    'cancel_url': os.getenv('PAYPAL_CANCEL_URL', 'http://localhost:3000/payment/cancel')
                },
                'transactions': [{
                    'amount': {
                        'currency': 'USD',
                        'total': str(amount)
                    },
                    'description': metadata.get('description', 'AgentShop Purchase')
                }]
            })
            
            if payment.create():
                # Find approval URL
                approval_url = None
                for link in payment.links:
                    if link.rel == 'approval_url':
                        approval_url = link.href
                        break
                
                return PaymentResult(
                    success=True,
                    transaction_id=payment.id,
                    raw_response={
                        'payment': payment,
                        'approval_url': approval_url
                    }
                )
            else:
                return PaymentResult(
                    success=False,
                    error_message=f"PayPal payment creation failed: {payment.error}",
                    raw_response=payment.error
                )
                
        except Exception as e:
            logger.error(f"PayPal payment processing error: {e}")
            return PaymentResult(
                success=False,
                error_message=str(e)
            )
    
    def execute_payment(self, payment_id: str, payer_id: str) -> PaymentResult:
        """Execute approved PayPal payment"""
        if not self.enabled:
            return PaymentResult(
                success=False,
                error_message="PayPal payment provider not configured"
            )
        
        try:
            payment = self.paypal.Payment.find(payment_id)
            
            if payment.execute({'payer_id': payer_id}):
                return PaymentResult(
                    success=True,
                    transaction_id=payment_id,
                    raw_response=payment
                )
            else:
                return PaymentResult(
                    success=False,
                    error_message=f"PayPal payment execution failed: {payment.error}",
                    raw_response=payment.error
                )
                
        except Exception as e:
            logger.error(f"PayPal payment execution error: {e}")
            return PaymentResult(
                success=False,
                error_message=str(e)
            )
    
    def refund_payment(self, transaction_id: str, amount: Decimal = None) -> PaymentResult:
        """Refund a PayPal payment"""
        if not self.enabled:
            return PaymentResult(
                success=False,
                error_message="PayPal payment provider not configured"
            )
        
        try:
            # Find the sale transaction
            payment = self.paypal.Payment.find(transaction_id)
            
            for transaction in payment.transactions:
                for related_resource in transaction.related_resources:
                    if hasattr(related_resource, 'sale'):
                        sale = related_resource.sale
                        
                        refund_data = {}
                        if amount is not None:
                            refund_data['amount'] = {
                                'currency': 'USD',
                                'total': str(amount)
                            }
                        
                        refund = sale.refund(refund_data)
                        
                        if refund:
                            return PaymentResult(
                                success=True,
                                transaction_id=refund.id,
                                raw_response=refund
                            )
                        else:
                            return PaymentResult(
                                success=False,
                                error_message="PayPal refund failed"
                            )
            
            return PaymentResult(
                success=False,
                error_message="No sale transaction found to refund"
            )
            
        except Exception as e:
            logger.error(f"PayPal refund error: {e}")
            return PaymentResult(
                success=False,
                error_message=str(e)
            )
    
    def verify_webhook(self, payload: str, signature: str) -> bool:
        """Verify PayPal webhook - basic implementation"""
        # PayPal webhook verification is more complex and requires certificate validation
        # For now, we'll do basic validation
        try:
            data = json.loads(payload)
            return 'event_type' in data and 'resource' in data
        except Exception as e:
            logger.error(f"PayPal webhook verification failed: {e}")
            return False


class ManualPaymentProvider(BasePaymentProvider):
    """Manual payment provider for bank transfers, checks, etc."""
    
    def __init__(self):
        super().__init__()
        self.enabled = True
    
    def process_payment(self, amount: Decimal, payment_method: Dict[str, Any], 
                       metadata: Dict[str, Any] = None) -> PaymentResult:
        """Process manual payment (mark as pending)"""
        # Manual payments are always marked as pending for admin review
        transaction_id = f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{amount}"
        
        return PaymentResult(
            success=True,
            transaction_id=transaction_id,
            raw_response={
                'status': 'pending_manual_review',
                'payment_method': payment_method.get('type', 'manual'),
                'instructions': metadata.get('instructions', 'Please process manually')
            }
        )
    
    def refund_payment(self, transaction_id: str, amount: Decimal = None) -> PaymentResult:
        """Manual payment refunds must be processed manually"""
        return PaymentResult(
            success=True,
            transaction_id=f"refund_{transaction_id}",
            raw_response={
                'status': 'pending_manual_refund',
                'original_transaction': transaction_id,
                'refund_amount': str(amount) if amount else 'full'
            }
        )
    
    def verify_webhook(self, payload: str, signature: str) -> bool:
        """Manual payments don't have webhooks"""
        return False


class PaymentService:
    """Main payment service that orchestrates different payment providers"""
    
    def __init__(self):
        self.providers = {
            'stripe': StripePaymentProvider(),
            'paypal': PayPalPaymentProvider(),
            'manual': ManualPaymentProvider()
        }
    
    def get_available_providers(self) -> Dict[str, bool]:
        """Get list of available payment providers"""
        return {name: provider.enabled for name, provider in self.providers.items()}
    
    def process_payment(self, provider_name: str, amount: Decimal, 
                       payment_method: Dict[str, Any], 
                       metadata: Dict[str, Any] = None) -> PaymentResult:
        """Process payment with specified provider"""
        provider = self.providers.get(provider_name)
        if not provider:
            return PaymentResult(
                success=False,
                error_message=f"Unknown payment provider: {provider_name}"
            )
        
        if not provider.enabled:
            return PaymentResult(
                success=False,
                error_message=f"Payment provider {provider_name} is not enabled"
            )
        
        logger.info(f"Processing payment of ${amount} with {provider_name}")
        return provider.process_payment(amount, payment_method, metadata)
    
    def refund_payment(self, provider_name: str, transaction_id: str, 
                      amount: Decimal = None) -> PaymentResult:
        """Refund payment with specified provider"""
        provider = self.providers.get(provider_name)
        if not provider:
            return PaymentResult(
                success=False,
                error_message=f"Unknown payment provider: {provider_name}"
            )
        
        if not provider.enabled:
            return PaymentResult(
                success=False,
                error_message=f"Payment provider {provider_name} is not enabled"
            )
        
        logger.info(f"Processing refund for transaction {transaction_id} with {provider_name}")
        return provider.refund_payment(transaction_id, amount)
    
    def calculate_tax(self, amount: Decimal, billing_address: Dict[str, Any]) -> Decimal:
        """Calculate tax based on billing address"""
        try:
            # Simple tax calculation - in production, use a tax service like TaxJar
            tax_rate = Decimal('0.0')
            
            state = billing_address.get('state', '').upper()
            country = billing_address.get('country', '').upper()
            
            # US tax rates (simplified)
            if country == 'US':
                us_tax_rates = {
                    'CA': Decimal('0.0875'),  # California
                    'NY': Decimal('0.08'),    # New York
                    'TX': Decimal('0.0625'),  # Texas
                    'FL': Decimal('0.06'),    # Florida
                    'WA': Decimal('0.065'),   # Washington
                }
                tax_rate = us_tax_rates.get(state, Decimal('0.05'))  # Default 5%
            
            # EU VAT (simplified)
            elif country in ['GB', 'UK']:
                tax_rate = Decimal('0.20')  # UK VAT
            elif country in ['DE', 'FR', 'IT', 'ES']:
                tax_rate = Decimal('0.19')  # EU VAT (simplified)
            
            return amount * tax_rate
            
        except Exception as e:
            logger.error(f"Tax calculation error: {e}")
            return Decimal('0.0')
    
    def verify_webhook(self, provider_name: str, payload: str, signature: str) -> bool:
        """Verify webhook from payment provider"""
        provider = self.providers.get(provider_name)
        if not provider:
            return False
        
        return provider.verify_webhook(payload, signature)


# Global payment service instance
payment_service = PaymentService()