#!/usr/bin/env python3
"""
Data and Database-related Exceptions

Specialized exceptions for database operations, data validation, and migration errors.
"""

from typing import Optional, Dict, Any, List
from .base_exceptions import AgentShopError, ValidationError


class DatabaseError(AgentShopError):
    """Base exception for database-related errors."""
    
    def __init__(self, 
                 message: str = "Database Error",
                 operation: Optional[str] = None,
                 table: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
            **kwargs
        )
        self.operation = operation
        self.table = table
        
        self.details.update({
            'operation': operation,
            'table': table
        })


class ConnectionError(DatabaseError):
    """Exception for database connection failures."""
    
    def __init__(self, 
                 message: str = "Database Connection Error",
                 database_url: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "DB_CONNECTION_ERROR"
        self.database_url = database_url
        
        if database_url:
            # Hide credentials in URL
            safe_url = database_url.split('@')[-1] if '@' in database_url else database_url
            self.details['database_url'] = safe_url


class TransactionError(DatabaseError):
    """Exception for database transaction failures."""
    
    def __init__(self, 
                 message: str = "Transaction Error",
                 transaction_id: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "TRANSACTION_ERROR"
        self.transaction_id = transaction_id
        
        if transaction_id:
            self.details['transaction_id'] = transaction_id


class IntegrityError(DatabaseError):
    """Exception for database integrity constraint violations."""
    
    def __init__(self, 
                 message: str = "Integrity Constraint Violation",
                 constraint: Optional[str] = None,
                 constraint_type: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "INTEGRITY_ERROR"
        self.status_code = 409
        self.constraint = constraint
        self.constraint_type = constraint_type
        
        self.details.update({
            'constraint': constraint,
            'constraint_type': constraint_type
        })


class UniqueConstraintError(IntegrityError):
    """Exception for unique constraint violations."""
    
    def __init__(self, 
                 message: str = "Unique Constraint Violation",
                 field: Optional[str] = None,
                 value: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            constraint_type="unique",
            **kwargs
        )
        self.error_code = "UNIQUE_CONSTRAINT_ERROR"
        self.field = field
        self.value = value
        
        self.details.update({
            'field': field,
            'value': value
        })


class ForeignKeyError(IntegrityError):
    """Exception for foreign key constraint violations."""
    
    def __init__(self, 
                 message: str = "Foreign Key Constraint Violation",
                 foreign_key: Optional[str] = None,
                 referenced_table: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            constraint_type="foreign_key",
            **kwargs
        )
        self.error_code = "FOREIGN_KEY_ERROR"
        self.foreign_key = foreign_key
        self.referenced_table = referenced_table
        
        self.details.update({
            'foreign_key': foreign_key,
            'referenced_table': referenced_table
        })


class DataValidationError(ValidationError):
    """Exception for data validation failures."""
    
    def __init__(self, 
                 message: str = "Data Validation Error",
                 model: Optional[str] = None,
                 validation_type: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "DATA_VALIDATION_ERROR"
        self.model = model
        self.validation_type = validation_type
        
        self.details.update({
            'model': model,
            'validation_type': validation_type
        })


class DataIntegrityError(DatabaseError):
    """Exception for data integrity violations."""
    
    def __init__(self, 
                 message: str = "Data Integrity Error",
                 integrity_type: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "DATA_INTEGRITY_ERROR"
        self.integrity_type = integrity_type
        
        if integrity_type:
            self.details['integrity_type'] = integrity_type


class MigrationError(DatabaseError):
    """Exception for database migration failures."""
    
    def __init__(self, 
                 message: str = "Migration Error",
                 migration_version: Optional[str] = None,
                 migration_name: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "MIGRATION_ERROR"
        self.migration_version = migration_version
        self.migration_name = migration_name
        
        self.details.update({
            'migration_version': migration_version,
            'migration_name': migration_name
        })


class QueryError(DatabaseError):
    """Exception for SQL query execution errors."""
    
    def __init__(self, 
                 message: str = "Query Execution Error",
                 query: Optional[str] = None,
                 query_parameters: Optional[Dict[str, Any]] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "QUERY_ERROR"
        self.query = query
        self.query_parameters = query_parameters
        
        # Don't include sensitive data in details
        if query and len(query) < 500:  # Only include short queries
            self.details['query'] = query


class RecordNotFoundError(DatabaseError):
    """Exception for when a database record is not found."""
    
    def __init__(self, 
                 message: str = "Record Not Found",
                 model: Optional[str] = None,
                 identifier: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "RECORD_NOT_FOUND"
        self.status_code = 404
        self.model = model
        self.identifier = identifier
        
        self.details.update({
            'model': model,
            'identifier': identifier
        })


class RecordAlreadyExistsError(DatabaseError):
    """Exception for when attempting to create a record that already exists."""
    
    def __init__(self, 
                 message: str = "Record Already Exists",
                 model: Optional[str] = None,
                 identifier: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "RECORD_ALREADY_EXISTS"
        self.status_code = 409
        self.model = model
        self.identifier = identifier
        
        self.details.update({
            'model': model,
            'identifier': identifier
        })


class ConcurrencyError(DatabaseError):
    """Exception for concurrent modification conflicts."""
    
    def __init__(self, 
                 message: str = "Concurrent Modification Detected",
                 model: Optional[str] = None,
                 record_id: Optional[str] = None,
                 expected_version: Optional[int] = None,
                 actual_version: Optional[int] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "CONCURRENCY_ERROR"
        self.status_code = 409
        self.model = model
        self.record_id = record_id
        self.expected_version = expected_version
        self.actual_version = actual_version
        
        self.details.update({
            'model': model,
            'record_id': record_id,
            'expected_version': expected_version,
            'actual_version': actual_version
        })


class SchemaError(DatabaseError):
    """Exception for database schema-related errors."""
    
    def __init__(self, 
                 message: str = "Schema Error",
                 schema_object: Optional[str] = None,
                 schema_operation: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "SCHEMA_ERROR"
        self.schema_object = schema_object
        self.schema_operation = schema_operation
        
        self.details.update({
            'schema_object': schema_object,
            'schema_operation': schema_operation
        })


class BackupError(DatabaseError):
    """Exception for database backup operations."""
    
    def __init__(self, 
                 message: str = "Backup Error",
                 backup_type: Optional[str] = None,
                 backup_path: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "BACKUP_ERROR"
        self.backup_type = backup_type
        self.backup_path = backup_path
        
        self.details.update({
            'backup_type': backup_type,
            'backup_path': backup_path
        })


class RestoreError(DatabaseError):
    """Exception for database restore operations."""
    
    def __init__(self, 
                 message: str = "Restore Error",
                 restore_source: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "RESTORE_ERROR"
        self.restore_source = restore_source
        
        if restore_source:
            self.details['restore_source'] = restore_source


# Utility functions for data error handling

def create_unique_constraint_error(field: str, value: str, model: str = None) -> UniqueConstraintError:
    """
    Create a unique constraint error with standard message format.
    
    Args:
        field: Field name that violated the constraint
        value: Value that caused the violation
        model: Model name
        
    Returns:
        UniqueConstraintError instance
    """
    if model:
        message = f"{model} with {field} '{value}' already exists"
    else:
        message = f"Value '{value}' already exists for field '{field}'"
    
    return UniqueConstraintError(
        message=message,
        field=field,
        value=value,
        table=model
    )


def create_foreign_key_error(foreign_key: str, 
                           referenced_table: str, 
                           model: str = None) -> ForeignKeyError:
    """
    Create a foreign key constraint error with standard message format.
    
    Args:
        foreign_key: Foreign key field name
        referenced_table: Referenced table name
        model: Model name
        
    Returns:
        ForeignKeyError instance
    """
    if model:
        message = f"Invalid {foreign_key} reference in {model} to {referenced_table}"
    else:
        message = f"Invalid foreign key reference: {foreign_key} -> {referenced_table}"
    
    return ForeignKeyError(
        message=message,
        foreign_key=foreign_key,
        referenced_table=referenced_table,
        table=model
    )


def create_record_not_found_error(model: str, identifier: str) -> RecordNotFoundError:
    """
    Create a record not found error with standard message format.
    
    Args:
        model: Model name
        identifier: Record identifier
        
    Returns:
        RecordNotFoundError instance
    """
    message = f"{model} with identifier '{identifier}' not found"
    
    return RecordNotFoundError(
        message=message,
        model=model,
        identifier=identifier
    )