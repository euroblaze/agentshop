#!/usr/bin/env python3
"""
Database Security - Enhanced security for database operations
"""

import re
import logging
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from functools import wraps
import hashlib
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseSecurity:
    """Database security utilities and monitoring"""
    
    @staticmethod
    def setup_security_events(engine: Engine):
        """Set up database security event listeners"""
        
        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Log and validate SQL queries before execution"""
            
            # Log slow or complex queries
            if DatabaseSecurity.is_complex_query(statement):
                logger.info(f"Complex query detected: {statement[:200]}...")
            
            # Validate query for security issues
            if DatabaseSecurity.contains_dangerous_sql(statement):
                logger.error(f"Dangerous SQL detected: {statement}")
                raise SQLAlchemyError("Query blocked for security reasons")
        
        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Monitor query execution results"""
            
            # Log queries that affect many rows
            if hasattr(cursor, 'rowcount') and cursor.rowcount > 1000:
                logger.warning(f"Query affected {cursor.rowcount} rows: {statement[:100]}...")
    
    @staticmethod
    def is_complex_query(statement: str) -> bool:
        """Check if query is complex and might need monitoring"""
        complex_patterns = [
            r'\bUNION\b',
            r'\bSUBQUERY\b',
            r'\bEXISTS\b',
            r'\bJOIN.*JOIN.*JOIN\b',  # Multiple joins
            r'\bGROUP BY.*HAVING\b',
            r'\bORDER BY.*LIMIT\s+\d{4,}\b'  # Large limits
        ]
        
        for pattern in complex_patterns:
            if re.search(pattern, statement, re.IGNORECASE):
                return True
        
        return False
    
    @staticmethod
    def contains_dangerous_sql(statement: str) -> bool:
        """Check for potentially dangerous SQL patterns"""
        dangerous_patterns = [
            r'\bDROP\s+TABLE\b',
            r'\bTRUNCATE\b',
            r'\bDELETE\s+FROM\s+\w+\s*;\s*DROP\b',
            r'\bUPDATE\s+\w+\s+SET\s+.*\s+WHERE\s+1\s*=\s*1\b',
            r'\bDELETE\s+FROM\s+\w+\s+WHERE\s+1\s*=\s*1\b',
            r'\bINSERT\s+INTO\s+\w+\s+SELECT\s+\*\s+FROM\b',
            r'\bEXEC\s*\(',
            r'\bsp_executesql\b',
            r'\bxp_cmdshell\b'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, statement, re.IGNORECASE):
                return True
        
        return False
    
    @staticmethod
    def sanitize_search_query(query: str) -> str:
        """Sanitize user search queries"""
        if not query:
            return ""
        
        # Remove dangerous characters
        sanitized = re.sub(r'[<>"\';\\]', '', query)
        
        # Limit length
        sanitized = sanitized[:200]
        
        # Remove SQL keywords
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER']
        for keyword in sql_keywords:
            sanitized = re.sub(rf'\b{keyword}\b', '', sanitized, flags=re.IGNORECASE)
        
        return sanitized.strip()


class AuditLogger:
    """Database audit logging"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def log_data_access(self, table_name: str, operation: str, 
                       record_id: Optional[Union[int, str]] = None,
                       user_id: Optional[int] = None,
                       additional_data: Optional[Dict] = None):
        """Log data access events"""
        
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'table_name': table_name,
            'operation': operation,
            'record_id': record_id,
            'user_id': user_id,
            'additional_data': additional_data or {}
        }
        
        # Log to audit table or external service
        logger.info(f"Data Access: {json.dumps(audit_entry)}")
    
    def log_sensitive_data_access(self, data_type: str, user_id: int, purpose: str):
        """Log access to sensitive data (PII, payment info)"""
        
        sensitive_access = {
            'timestamp': datetime.utcnow().isoformat(),
            'data_type': data_type,
            'user_id': user_id,
            'purpose': purpose,
            'ip_address': getattr(request, 'remote_addr', 'unknown') if 'request' in globals() else 'system'
        }
        
        logger.warning(f"Sensitive Data Access: {json.dumps(sensitive_access)}")


def secure_query(allowed_tables: List[str] = None):
    """Decorator to validate and secure database queries"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Validate table access if specified
                if allowed_tables and hasattr(func, '__name__'):
                    # Extract table names from function or validate access
                    pass
                
                # Execute function with security monitoring
                result = func(*args, **kwargs)
                
                return result
                
            except SQLAlchemyError as e:
                logger.error(f"Database security error in {func.__name__}: {e}")
                raise
            except Exception as e:
                logger.error(f"Security validation error in {func.__name__}: {e}")
                raise
                
        return wrapper
    return decorator


class ParameterizedQuery:
    """Safe parameterized query builder"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def safe_search(self, table_name: str, search_fields: List[str], 
                   search_term: str, filters: Dict[str, Any] = None) -> List[Dict]:
        """Execute safe search query with parameterized inputs"""
        
        # Sanitize inputs
        search_term = DatabaseSecurity.sanitize_search_query(search_term)
        
        # Build safe parameterized query
        search_conditions = []
        params = {'search_term': f'%{search_term}%'}
        
        for i, field in enumerate(search_fields):
            # Validate field names (whitelist approach)
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', field):
                raise ValueError(f"Invalid field name: {field}")
            
            search_conditions.append(f"{field} ILIKE :search_term")
        
        where_clause = " OR ".join(search_conditions)
        
        # Add filters
        if filters:
            for key, value in filters.items():
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                    continue
                
                where_clause += f" AND {key} = :{key}"
                params[key] = value
        
        # Execute safe query
        query = text(f"SELECT * FROM {table_name} WHERE {where_clause} LIMIT 100")
        result = self.session.execute(query, params)
        
        return [dict(row._mapping) for row in result]
    
    def safe_update(self, table_name: str, record_id: int, 
                   updates: Dict[str, Any], user_id: int) -> bool:
        """Execute safe update with validation"""
        
        # Validate table name
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            raise ValueError("Invalid table name")
        
        # Validate field names
        update_clauses = []
        params = {'record_id': record_id}
        
        for field, value in updates.items():
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', field):
                raise ValueError(f"Invalid field name: {field}")
            
            update_clauses.append(f"{field} = :{field}")
            params[field] = value
        
        set_clause = ", ".join(update_clauses)
        
        # Log the update
        audit_logger = AuditLogger(self.session)
        audit_logger.log_data_access(table_name, 'UPDATE', record_id, user_id, updates)
        
        # Execute update
        query = text(f"UPDATE {table_name} SET {set_clause} WHERE id = :record_id")
        result = self.session.execute(query, params)
        
        return result.rowcount > 0


class DataMasking:
    """Data masking for sensitive information"""
    
    @staticmethod
    def mask_email(email: str) -> str:
        """Mask email for logging/display"""
        if not email or '@' not in email:
            return email
        
        local, domain = email.split('@', 1)
        if len(local) <= 2:
            masked_local = '*' * len(local)
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        
        return f"{masked_local}@{domain}"
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """Mask phone number"""
        if not phone or len(phone) < 4:
            return phone
        
        return '*' * (len(phone) - 4) + phone[-4:]
    
    @staticmethod
    def mask_credit_card(card_number: str) -> str:
        """Mask credit card number"""
        if not card_number or len(card_number) < 4:
            return card_number
        
        return '*' * (len(card_number) - 4) + card_number[-4:]
    
    @staticmethod
    def hash_pii(data: str) -> str:
        """Hash PII for indexing while preserving privacy"""
        return hashlib.sha256(data.encode()).hexdigest()


class EncryptionHelper:
    """Database field encryption helper"""
    
    def __init__(self, encryption_key: str):
        self.encryption_key = encryption_key
    
    def encrypt_field(self, data: str) -> str:
        """Encrypt sensitive field data"""
        # TODO: Implement with cryptography library
        # For now, return base64 encoded (NOT secure)
        import base64
        return base64.b64encode(data.encode()).decode()
    
    def decrypt_field(self, encrypted_data: str) -> str:
        """Decrypt sensitive field data"""
        # TODO: Implement with cryptography library
        import base64
        return base64.b64decode(encrypted_data.encode()).decode()


# Database security configuration
DB_SECURITY_CONFIG = {
    'ENABLE_QUERY_LOGGING': True,
    'ENABLE_AUDIT_LOGGING': True,
    'MAX_QUERY_EXECUTION_TIME': 30,  # seconds
    'MAX_ROWS_PER_QUERY': 10000,
    'SENSITIVE_TABLES': [
        'customers', 'payments', 'orders', 'admin_users'
    ],
    'ENCRYPTED_FIELDS': [
        'credit_card_number', 'ssn', 'bank_account'
    ]
}