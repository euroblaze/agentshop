#!/usr/bin/env python3
"""
Email Service - Handles all email communications for the application
"""

import smtplib
import logging
from typing import List, Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailService:
    """Service for handling email operations"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp-relay.brevo.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@agentshop.com')
        self.admin_email = os.getenv('ADMIN_EMAIL', 'admin@agentshop.com')
        
    def _create_smtp_connection(self) -> smtplib.SMTP:
        """Create and configure SMTP connection"""
        try:
            smtp = smtplib.SMTP(self.smtp_server, self.smtp_port)
            smtp.starttls()
            if self.smtp_user:
                smtp.login(self.smtp_user, self.smtp_password)
            return smtp
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {e}")
            raise
    
    def _load_email_template(self, template_name: str) -> Dict[str, str]:
        """Load email template from file or database"""
        try:
            # Try to load from database first (if EmailTemplate model exists)
            from ..models.admin_models import EmailTemplate
            from ..repositories.admin_repository import AdminRepository
            from sqlalchemy.orm import sessionmaker
            from ..database import engine
            
            Session = sessionmaker(bind=engine)
            session = Session()
            
            try:
                admin_repo = AdminRepository(session)
                template = admin_repo.get_email_template(template_name)
                if template:
                    return {
                        'subject': template.subject,
                        'body_html': template.body_html,
                        'body_text': template.body_text
                    }
            finally:
                session.close()
        except Exception as e:
            logger.warning(f"Could not load template from database: {e}")
        
        # Fallback to file-based templates
        template_path = Path(__file__).parent.parent / 'templates' / 'email' / f'{template_name}.json'
        if template_path.exists():
            with open(template_path, 'r') as f:
                return json.load(f)
        
        # Default template
        return self._get_default_template(template_name)
    
    def _get_default_template(self, template_name: str) -> Dict[str, str]:
        """Get default email template"""
        templates = {
            'order_confirmation': {
                'subject': 'Order Confirmation - #{order_number}',
                'body_html': '''
                <h2>Thank you for your order!</h2>
                <p>Dear {customer_name},</p>
                <p>We have received your order #{order_number} and are processing it now.</p>
                <h3>Order Details:</h3>
                <p>Order Number: {order_number}</p>
                <p>Order Date: {order_date}</p>
                <p>Total Amount: ${total_amount}</p>
                <h3>Items Ordered:</h3>
                {items_html}
                <p>You will receive another email when your order ships.</p>
                <p>Thank you for choosing AgentShop!</p>
                ''',
                'body_text': '''
                Thank you for your order!
                
                Dear {customer_name},
                
                We have received your order #{order_number} and are processing it now.
                
                Order Details:
                Order Number: {order_number}
                Order Date: {order_date}
                Total Amount: ${total_amount}
                
                Items Ordered:
                {items_text}
                
                You will receive another email when your order ships.
                
                Thank you for choosing AgentShop!
                '''
            },
            'installation_request': {
                'subject': 'New Installation Request - #{order_number}',
                'body_html': '''
                <h2>New Installation Request</h2>
                <p>A new installation request has been submitted:</p>
                <p><strong>Order:</strong> {order_number}</p>
                <p><strong>Customer:</strong> {customer_name}</p>
                <p><strong>Product:</strong> {product_name}</p>
                <p><strong>Request Date:</strong> {request_date}</p>
                <p><strong>Notes:</strong> {notes}</p>
                <p>Please contact the customer to schedule the installation.</p>
                ''',
                'body_text': '''
                New Installation Request
                
                A new installation request has been submitted:
                
                Order: {order_number}
                Customer: {customer_name}
                Product: {product_name}
                Request Date: {request_date}
                Notes: {notes}
                
                Please contact the customer to schedule the installation.
                '''
            },
            'installation_quote': {
                'subject': 'Installation Quote - #{order_number}',
                'body_html': '''
                <h2>Installation Quote</h2>
                <p>Dear {customer_name},</p>
                <p>Thank you for your installation request for {product_name}.</p>
                <p><strong>Quote Amount:</strong> ${quote_amount}</p>
                <p><strong>Estimated Time:</strong> {estimated_hours} hours</p>
                <p>Our team will contact you shortly to schedule the installation.</p>
                <p>Best regards,<br>AgentShop Installation Team</p>
                ''',
                'body_text': '''
                Installation Quote
                
                Dear {customer_name},
                
                Thank you for your installation request for {product_name}.
                
                Quote Amount: ${quote_amount}
                Estimated Time: {estimated_hours} hours
                
                Our team will contact you shortly to schedule the installation.
                
                Best regards,
                AgentShop Installation Team
                '''
            },
            'user_registration': {
                'subject': 'Welcome to AgentShop!',
                'body_html': '''
                <h2>Welcome to AgentShop!</h2>
                <p>Dear {customer_name},</p>
                <p>Thank you for registering with AgentShop. Your account has been successfully created.</p>
                <p><strong>Your Account Details:</strong></p>
                <p>Email: {email}</p>
                <p>Registration Date: {registration_date}</p>
                <p>You can now browse our products and make purchases.</p>
                <p>Welcome aboard!</p>
                ''',
                'body_text': '''
                Welcome to AgentShop!
                
                Dear {customer_name},
                
                Thank you for registering with AgentShop. Your account has been successfully created.
                
                Your Account Details:
                Email: {email}
                Registration Date: {registration_date}
                
                You can now browse our products and make purchases.
                
                Welcome aboard!
                '''
            }
        }
        
        return templates.get(template_name, {
            'subject': 'Notification from AgentShop',
            'body_html': '<p>This is a notification from AgentShop.</p>',
            'body_text': 'This is a notification from AgentShop.'
        })
    
    def _format_template(self, template: Dict[str, str], variables: Dict[str, Any]) -> Dict[str, str]:
        """Format template with variables"""
        try:
            return {
                'subject': template['subject'].format(**variables),
                'body_html': template['body_html'].format(**variables),
                'body_text': template['body_text'].format(**variables)
            }
        except KeyError as e:
            logger.error(f"Missing template variable: {e}")
            return template
    
    def send_order_confirmation(self, order_data: Dict[str, Any]) -> bool:
        """Send order confirmation email"""
        try:
            # Prepare items list
            items_html = ""
            items_text = ""
            
            if 'items' in order_data:
                for item in order_data['items']:
                    items_html += f"<p>• {item.get('name', 'Product')} - ${item.get('price', '0.00')}</p>"
                    items_text += f"• {item.get('name', 'Product')} - ${item.get('price', '0.00')}\n"
            
            variables = {
                'customer_name': order_data.get('customer_name', 'Customer'),
                'order_number': order_data.get('order_number', 'N/A'),
                'order_date': order_data.get('order_date', datetime.now().strftime('%Y-%m-%d')),
                'total_amount': order_data.get('total_amount', '0.00'),
                'items_html': items_html,
                'items_text': items_text
            }
            
            template = self._load_email_template('order_confirmation')
            formatted = self._format_template(template, variables)
            
            return self._send_email(
                to_email=order_data.get('customer_email', ''),
                subject=formatted['subject'],
                body_html=formatted['body_html'],
                body_text=formatted['body_text']
            )
            
        except Exception as e:
            logger.error(f"Failed to send order confirmation: {e}")
            return False
    
    def send_installation_request_notification(self, request_data: Dict[str, Any]) -> bool:
        """Send installation request notification to admin"""
        try:
            variables = {
                'order_number': request_data.get('order_number', 'N/A'),
                'customer_name': request_data.get('customer_name', 'Customer'),
                'product_name': request_data.get('product_name', 'Product'),
                'request_date': request_data.get('request_date', datetime.now().strftime('%Y-%m-%d')),
                'notes': request_data.get('notes', 'No additional notes')
            }
            
            template = self._load_email_template('installation_request')
            formatted = self._format_template(template, variables)
            
            return self._send_email(
                to_email=self.admin_email,
                subject=formatted['subject'],
                body_html=formatted['body_html'],
                body_text=formatted['body_text']
            )
            
        except Exception as e:
            logger.error(f"Failed to send installation request notification: {e}")
            return False
    
    def send_installation_quote(self, quote_data: Dict[str, Any]) -> bool:
        """Send installation quote to customer"""
        try:
            variables = {
                'customer_name': quote_data.get('customer_name', 'Customer'),
                'order_number': quote_data.get('order_number', 'N/A'),
                'product_name': quote_data.get('product_name', 'Product'),
                'quote_amount': quote_data.get('quote_amount', '0.00'),
                'estimated_hours': quote_data.get('estimated_hours', 'TBD')
            }
            
            template = self._load_email_template('installation_quote')
            formatted = self._format_template(template, variables)
            
            return self._send_email(
                to_email=quote_data.get('customer_email', ''),
                subject=formatted['subject'],
                body_html=formatted['body_html'],
                body_text=formatted['body_text']
            )
            
        except Exception as e:
            logger.error(f"Failed to send installation quote: {e}")
            return False
    
    def send_registration_welcome(self, customer_data: Dict[str, Any]) -> bool:
        """Send welcome email to new customer"""
        try:
            variables = {
                'customer_name': customer_data.get('first_name', 'Customer'),
                'email': customer_data.get('email', ''),
                'registration_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            template = self._load_email_template('user_registration')
            formatted = self._format_template(template, variables)
            
            return self._send_email(
                to_email=customer_data.get('email', ''),
                subject=formatted['subject'],
                body_html=formatted['body_html'],
                body_text=formatted['body_text']
            )
            
        except Exception as e:
            logger.error(f"Failed to send registration welcome email: {e}")
            return False
    
    def _send_email(self, to_email: str, subject: str, 
                   body_html: str = None, body_text: str = None,
                   attachments: List[str] = None) -> bool:
        """Send email with HTML and text content"""
        try:
            if not to_email:
                logger.error("No recipient email provided")
                return False
                
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Add text content
            if body_text:
                text_part = MIMEText(body_text, 'plain')
                msg.attach(text_part)
            
            # Add HTML content
            if body_html:
                html_part = MIMEText(body_html, 'html')
                msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {os.path.basename(file_path)}'
                            )
                            msg.attach(part)
            
            # Send email
            with self._create_smtp_connection() as smtp:
                smtp.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_custom_email(self, to_email: str, subject: str, message: str, 
                         is_html: bool = False) -> bool:
        """Send custom email"""
        try:
            if is_html:
                return self._send_email(to_email, subject, body_html=message)
            else:
                return self._send_email(to_email, subject, body_text=message)
        except Exception as e:
            logger.error(f"Failed to send custom email: {e}")
            return False


# Global email service instance
email_service = EmailService()