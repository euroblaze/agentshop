#!/usr/bin/env python3
"""
JSON Schema Validation

Provides comprehensive schema-based validation for request data and complex objects.
"""

import re
from typing import Dict, List, Any, Optional, Union, Callable
from abc import ABC, abstractmethod


class SchemaValidationError(Exception):
    """Exception raised for schema validation errors."""
    
    def __init__(self, message: str, field_errors: Optional[Dict[str, List[str]]] = None):
        super().__init__(message)
        self.field_errors = field_errors or {}


class FieldValidator(ABC):
    """Abstract base class for field validators."""
    
    @abstractmethod
    def validate(self, value: Any, field_name: str) -> List[str]:
        """Validate field value and return list of errors."""
        pass


class TypeValidator(FieldValidator):
    """Validates field type."""
    
    def __init__(self, expected_type: str):
        self.expected_type = expected_type
        self.type_map = {
            'string': str,
            'integer': int,
            'number': (int, float),
            'boolean': bool,
            'array': list,
            'object': dict,
            'null': type(None)
        }
    
    def validate(self, value: Any, field_name: str) -> List[str]:
        """Validate field type."""
        if self.expected_type not in self.type_map:
            return [f"Unknown type '{self.expected_type}' for field '{field_name}'"]
        
        expected_python_type = self.type_map[self.expected_type]
        
        if not isinstance(value, expected_python_type):
            return [f"Field '{field_name}' must be of type {self.expected_type}"]
        
        return []


class LengthValidator(FieldValidator):
    """Validates string length or array/object size."""
    
    def __init__(self, min_length: Optional[int] = None, max_length: Optional[int] = None):
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, value: Any, field_name: str) -> List[str]:
        """Validate length constraints."""
        errors = []
        
        if hasattr(value, '__len__'):
            length = len(value)
            
            if self.min_length is not None and length < self.min_length:
                errors.append(f"Field '{field_name}' must have at least {self.min_length} characters/items")
            
            if self.max_length is not None and length > self.max_length:
                errors.append(f"Field '{field_name}' must have no more than {self.max_length} characters/items")
        
        return errors


class RangeValidator(FieldValidator):
    """Validates numeric range."""
    
    def __init__(self, minimum: Optional[Union[int, float]] = None, 
                 maximum: Optional[Union[int, float]] = None,
                 exclusive_minimum: bool = False,
                 exclusive_maximum: bool = False):
        self.minimum = minimum
        self.maximum = maximum
        self.exclusive_minimum = exclusive_minimum
        self.exclusive_maximum = exclusive_maximum
    
    def validate(self, value: Any, field_name: str) -> List[str]:
        """Validate numeric range."""
        errors = []
        
        if isinstance(value, (int, float)):
            if self.minimum is not None:
                if self.exclusive_minimum:
                    if value <= self.minimum:
                        errors.append(f"Field '{field_name}' must be greater than {self.minimum}")
                else:
                    if value < self.minimum:
                        errors.append(f"Field '{field_name}' must be at least {self.minimum}")
            
            if self.maximum is not None:
                if self.exclusive_maximum:
                    if value >= self.maximum:
                        errors.append(f"Field '{field_name}' must be less than {self.maximum}")
                else:
                    if value > self.maximum:
                        errors.append(f"Field '{field_name}' must be no more than {self.maximum}")
        
        return errors


class PatternValidator(FieldValidator):
    """Validates string pattern using regex."""
    
    def __init__(self, pattern: str, flags: int = 0):
        self.pattern = pattern
        self.regex = re.compile(pattern, flags)
    
    def validate(self, value: Any, field_name: str) -> List[str]:
        """Validate string pattern."""
        if isinstance(value, str) and not self.regex.match(value):
            return [f"Field '{field_name}' format is invalid"]
        return []


class EnumValidator(FieldValidator):
    """Validates enum values."""
    
    def __init__(self, allowed_values: List[Any]):
        self.allowed_values = allowed_values
    
    def validate(self, value: Any, field_name: str) -> List[str]:
        """Validate enum value."""
        if value not in self.allowed_values:
            return [f"Field '{field_name}' must be one of: {', '.join(map(str, self.allowed_values))}"]
        return []


class CustomValidator(FieldValidator):
    """Custom validator using a callable."""
    
    def __init__(self, validator_func: Callable[[Any], Union[bool, str, List[str]]], 
                 error_message: str = "Field validation failed"):
        self.validator_func = validator_func
        self.error_message = error_message
    
    def validate(self, value: Any, field_name: str) -> List[str]:
        """Validate using custom function."""
        result = self.validator_func(value)
        
        if result is True:
            return []
        elif result is False:
            return [f"Field '{field_name}': {self.error_message}"]
        elif isinstance(result, str):
            return [f"Field '{field_name}': {result}"]
        elif isinstance(result, list):
            return [f"Field '{field_name}': {error}" for error in result]
        else:
            return [f"Field '{field_name}': {self.error_message}"]


class FieldSchema:
    """Schema definition for a single field."""
    
    def __init__(self, 
                 field_type: str = 'string',
                 required: bool = False,
                 nullable: bool = False,
                 default: Any = None,
                 validators: Optional[List[FieldValidator]] = None,
                 description: Optional[str] = None):
        self.field_type = field_type
        self.required = required
        self.nullable = nullable
        self.default = default
        self.validators = validators or []
        self.description = description
        
        # Add type validator
        self.validators.insert(0, TypeValidator(field_type))
    
    def add_validator(self, validator: FieldValidator):
        """Add a validator to this field."""
        self.validators.append(validator)
    
    def validate(self, value: Any, field_name: str) -> List[str]:
        """Validate field value."""
        # Handle null values
        if value is None:
            if self.nullable:
                return []
            elif self.required:
                return [f"Field '{field_name}' is required"]
            else:
                return []
        
        # Handle empty strings
        if isinstance(value, str) and not value.strip() and self.required:
            return [f"Field '{field_name}' cannot be empty"]
        
        # Run all validators
        errors = []
        for validator in self.validators:
            field_errors = validator.validate(value, field_name)
            errors.extend(field_errors)
        
        return errors


class JSONSchemaValidator:
    """JSON Schema validator for complex object validation."""
    
    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema
        self.fields = self._parse_schema(schema)
    
    def _parse_schema(self, schema: Dict[str, Any]) -> Dict[str, FieldSchema]:
        """Parse JSON schema into field schemas."""
        fields = {}
        properties = schema.get('properties', {})
        required_fields = set(schema.get('required', []))
        
        for field_name, field_def in properties.items():
            field_schema = self._create_field_schema(field_def, field_name in required_fields)
            fields[field_name] = field_schema
        
        return fields
    
    def _create_field_schema(self, field_def: Dict[str, Any], required: bool) -> FieldSchema:
        """Create field schema from JSON schema field definition."""
        field_type = field_def.get('type', 'string')
        nullable = field_def.get('nullable', False)
        default = field_def.get('default')
        description = field_def.get('description')
        
        field_schema = FieldSchema(
            field_type=field_type,
            required=required,
            nullable=nullable,
            default=default,
            description=description
        )
        
        # Add length constraints
        if 'minLength' in field_def or 'maxLength' in field_def:
            field_schema.add_validator(
                LengthValidator(field_def.get('minLength'), field_def.get('maxLength'))
            )
        
        # Add range constraints
        if 'minimum' in field_def or 'maximum' in field_def:
            field_schema.add_validator(
                RangeValidator(
                    field_def.get('minimum'),
                    field_def.get('maximum'),
                    field_def.get('exclusiveMinimum', False),
                    field_def.get('exclusiveMaximum', False)
                )
            )
        
        # Add pattern constraint
        if 'pattern' in field_def:
            field_schema.add_validator(PatternValidator(field_def['pattern']))
        
        # Add enum constraint
        if 'enum' in field_def:
            field_schema.add_validator(EnumValidator(field_def['enum']))
        
        return field_schema
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate data against schema."""
        errors = {}
        
        # Check for required fields
        for field_name, field_schema in self.fields.items():
            if field_schema.required and field_name not in data:
                errors[field_name] = [f"Field '{field_name}' is required"]
        
        # Validate each field
        for field_name, value in data.items():
            if field_name in self.fields:
                field_errors = self.fields[field_name].validate(value, field_name)
                if field_errors:
                    errors[field_name] = field_errors
            # Note: Unknown fields are allowed by default
        
        return errors
    
    def is_valid(self, data: Dict[str, Any]) -> bool:
        """Check if data is valid according to schema."""
        return len(self.validate(data)) == 0
    
    def get_field_schema(self, field_name: str) -> Optional[FieldSchema]:
        """Get schema for a specific field."""
        return self.fields.get(field_name)


# Convenience functions

def validate_request_data(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Validate request data against JSON schema.
    
    Args:
        data: Request data to validate
        schema: JSON schema definition
        
    Returns:
        Dictionary of validation errors
    """
    validator = JSONSchemaValidator(schema)
    return validator.validate(data)


def validate_field(value: Any, field_type: str, **constraints) -> List[str]:
    """
    Validate a single field value.
    
    Args:
        value: Value to validate
        field_type: Type of the field ('string', 'integer', etc.)
        **constraints: Additional constraints (min_length, pattern, etc.)
        
    Returns:
        List of validation errors
    """
    field_schema = FieldSchema(field_type=field_type)
    
    # Add constraints as validators
    if 'min_length' in constraints or 'max_length' in constraints:
        field_schema.add_validator(
            LengthValidator(constraints.get('min_length'), constraints.get('max_length'))
        )
    
    if 'minimum' in constraints or 'maximum' in constraints:
        field_schema.add_validator(
            RangeValidator(constraints.get('minimum'), constraints.get('maximum'))
        )
    
    if 'pattern' in constraints:
        field_schema.add_validator(PatternValidator(constraints['pattern']))
    
    if 'enum' in constraints:
        field_schema.add_validator(EnumValidator(constraints['enum']))
    
    return field_schema.validate(value, 'value')


def create_schema(fields: Dict[str, Dict[str, Any]], required: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Create a JSON schema from field definitions.
    
    Args:
        fields: Dictionary of field definitions
        required: List of required field names
        
    Returns:
        JSON schema dictionary
    """
    schema = {
        'type': 'object',
        'properties': fields
    }
    
    if required:
        schema['required'] = required
    
    return schema


# Common schema patterns

EMAIL_FIELD = {
    'type': 'string',
    'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    'maxLength': 255
}

PASSWORD_FIELD = {
    'type': 'string',
    'minLength': 8,
    'maxLength': 128
}

PHONE_FIELD = {
    'type': 'string',
    'pattern': r'^\+?1?\d{9,15}$'
}

URL_FIELD = {
    'type': 'string',
    'pattern': r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
}

SLUG_FIELD = {
    'type': 'string',
    'pattern': r'^[a-z0-9]+(?:-[a-z0-9]+)*$',
    'minLength': 1,
    'maxLength': 100
}

# Example schemas

USER_REGISTRATION_SCHEMA = create_schema({
    'first_name': {'type': 'string', 'minLength': 1, 'maxLength': 50},
    'last_name': {'type': 'string', 'minLength': 1, 'maxLength': 50},
    'email': EMAIL_FIELD,
    'password': PASSWORD_FIELD,
    'phone': {**PHONE_FIELD, 'nullable': True},
    'terms_accepted': {'type': 'boolean'}
}, required=['first_name', 'last_name', 'email', 'password', 'terms_accepted'])

USER_LOGIN_SCHEMA = create_schema({
    'email': EMAIL_FIELD,
    'password': {'type': 'string', 'minLength': 1}
}, required=['email', 'password'])

PRODUCT_SCHEMA = create_schema({
    'name': {'type': 'string', 'minLength': 1, 'maxLength': 200},
    'slug': SLUG_FIELD,
    'description': {'type': 'string', 'maxLength': 2000},
    'price': {'type': 'number', 'minimum': 0},
    'category_id': {'type': 'integer', 'minimum': 1},
    'is_active': {'type': 'boolean', 'default': True}
}, required=['name', 'slug', 'price', 'category_id'])