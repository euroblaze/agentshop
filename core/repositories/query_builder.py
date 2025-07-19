#!/usr/bin/env python3
"""
Query Builder - Advanced query construction utilities

Provides fluent interface for building complex database queries
with filters, joins, ordering, and pagination.
"""

from typing import Any, List, Optional, Dict, Union, Type
from sqlalchemy import and_, or_, not_, desc, asc, func
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql.elements import BinaryExpression
from enum import Enum
import operator

from ..orm import BaseModel


class FilterOperator(Enum):
    """Enumeration of supported filter operators."""
    EQ = "eq"           # Equal
    NE = "ne"           # Not equal
    GT = "gt"           # Greater than
    GTE = "gte"         # Greater than or equal
    LT = "lt"           # Less than
    LTE = "lte"         # Less than or equal
    LIKE = "like"       # SQL LIKE (case sensitive)
    ILIKE = "ilike"     # SQL ILIKE (case insensitive)
    IN = "in"           # IN clause
    NOT_IN = "not_in"   # NOT IN clause
    IS_NULL = "is_null" # IS NULL
    IS_NOT_NULL = "is_not_null"  # IS NOT NULL
    BETWEEN = "between" # BETWEEN clause
    STARTS_WITH = "starts_with"  # String starts with
    ENDS_WITH = "ends_with"      # String ends with
    CONTAINS = "contains"        # String contains


class FilterExpression:
    """
    Represents a single filter expression.
    
    Provides a fluent interface for building filter conditions
    that can be combined with AND/OR logic.
    """
    
    def __init__(self, field: str, operator: FilterOperator, value: Any):
        """
        Initialize filter expression.
        
        Args:
            field: Field name to filter on
            operator: Filter operator to apply
            value: Value to filter with
        """
        self.field = field
        self.operator = operator
        self.value = value
    
    def to_sqlalchemy(self, model_class: Type[BaseModel]) -> BinaryExpression:
        """
        Convert filter expression to SQLAlchemy expression.
        
        Args:
            model_class: Model class to build expression for
            
        Returns:
            SQLAlchemy binary expression
            
        Raises:
            ValueError: If field doesn't exist or operator is invalid
        """
        if not hasattr(model_class, self.field):
            raise ValueError(f"Field '{self.field}' not found in {model_class.__name__}")
        
        field = getattr(model_class, self.field)
        
        if self.operator == FilterOperator.EQ:
            return field == self.value
        elif self.operator == FilterOperator.NE:
            return field != self.value
        elif self.operator == FilterOperator.GT:
            return field > self.value
        elif self.operator == FilterOperator.GTE:
            return field >= self.value
        elif self.operator == FilterOperator.LT:
            return field < self.value
        elif self.operator == FilterOperator.LTE:
            return field <= self.value
        elif self.operator == FilterOperator.LIKE:
            return field.like(self.value)
        elif self.operator == FilterOperator.ILIKE:
            return field.ilike(self.value)
        elif self.operator == FilterOperator.IN:
            return field.in_(self.value)
        elif self.operator == FilterOperator.NOT_IN:
            return ~field.in_(self.value)
        elif self.operator == FilterOperator.IS_NULL:
            return field.is_(None)
        elif self.operator == FilterOperator.IS_NOT_NULL:
            return field.isnot(None)
        elif self.operator == FilterOperator.BETWEEN:
            if not isinstance(self.value, (list, tuple)) or len(self.value) != 2:
                raise ValueError("BETWEEN operator requires a list/tuple of 2 values")
            return field.between(self.value[0], self.value[1])
        elif self.operator == FilterOperator.STARTS_WITH:
            return field.ilike(f"{self.value}%")
        elif self.operator == FilterOperator.ENDS_WITH:
            return field.ilike(f"%{self.value}")
        elif self.operator == FilterOperator.CONTAINS:
            return field.ilike(f"%{self.value}%")
        else:
            raise ValueError(f"Unsupported operator: {self.operator}")
    
    @classmethod
    def eq(cls, field: str, value: Any) -> 'FilterExpression':
        """Create equals filter."""
        return cls(field, FilterOperator.EQ, value)
    
    @classmethod
    def ne(cls, field: str, value: Any) -> 'FilterExpression':
        """Create not equals filter."""
        return cls(field, FilterOperator.NE, value)
    
    @classmethod
    def gt(cls, field: str, value: Any) -> 'FilterExpression':
        """Create greater than filter."""
        return cls(field, FilterOperator.GT, value)
    
    @classmethod
    def gte(cls, field: str, value: Any) -> 'FilterExpression':
        """Create greater than or equal filter."""
        return cls(field, FilterOperator.GTE, value)
    
    @classmethod
    def lt(cls, field: str, value: Any) -> 'FilterExpression':
        """Create less than filter."""
        return cls(field, FilterOperator.LT, value)
    
    @classmethod
    def lte(cls, field: str, value: Any) -> 'FilterExpression':
        """Create less than or equal filter."""
        return cls(field, FilterOperator.LTE, value)
    
    @classmethod
    def like(cls, field: str, pattern: str) -> 'FilterExpression':
        """Create LIKE filter (case sensitive)."""
        return cls(field, FilterOperator.LIKE, pattern)
    
    @classmethod
    def ilike(cls, field: str, pattern: str) -> 'FilterExpression':
        """Create ILIKE filter (case insensitive)."""
        return cls(field, FilterOperator.ILIKE, pattern)
    
    @classmethod
    def in_(cls, field: str, values: List[Any]) -> 'FilterExpression':
        """Create IN filter."""
        return cls(field, FilterOperator.IN, values)
    
    @classmethod
    def not_in(cls, field: str, values: List[Any]) -> 'FilterExpression':
        """Create NOT IN filter."""
        return cls(field, FilterOperator.NOT_IN, values)
    
    @classmethod
    def is_null(cls, field: str) -> 'FilterExpression':
        """Create IS NULL filter."""
        return cls(field, FilterOperator.IS_NULL, None)
    
    @classmethod
    def is_not_null(cls, field: str) -> 'FilterExpression':
        """Create IS NOT NULL filter."""
        return cls(field, FilterOperator.IS_NOT_NULL, None)
    
    @classmethod
    def between(cls, field: str, start: Any, end: Any) -> 'FilterExpression':
        """Create BETWEEN filter."""
        return cls(field, FilterOperator.BETWEEN, [start, end])
    
    @classmethod
    def starts_with(cls, field: str, prefix: str) -> 'FilterExpression':
        """Create starts with filter."""
        return cls(field, FilterOperator.STARTS_WITH, prefix)
    
    @classmethod
    def ends_with(cls, field: str, suffix: str) -> 'FilterExpression':
        """Create ends with filter."""
        return cls(field, FilterOperator.ENDS_WITH, suffix)
    
    @classmethod
    def contains(cls, field: str, substring: str) -> 'FilterExpression':
        """Create contains filter."""
        return cls(field, FilterOperator.CONTAINS, substring)
    
    def __repr__(self) -> str:
        return f"FilterExpression({self.field} {self.operator.value} {self.value})"


class QueryBuilder:
    """
    Fluent interface for building complex database queries.
    
    Provides a chainable API for constructing queries with filters,
    joins, ordering, pagination, and aggregation.
    """
    
    def __init__(self, session: Session, model_class: Type[BaseModel]):
        """
        Initialize query builder.
        
        Args:
            session: Database session
            model_class: Model class to query
        """
        self.session = session
        self.model_class = model_class
        self._filters: List[FilterExpression] = []
        self._or_groups: List[List[FilterExpression]] = []
        self._order_by: List[tuple] = []  # (field, desc)
        self._limit: Optional[int] = None
        self._offset: int = 0
        self._group_by: List[str] = []
        self._having: List[FilterExpression] = []
        self._distinct: bool = False
    
    def filter(self, *expressions: FilterExpression) -> 'QueryBuilder':
        """
        Add filter expressions (combined with AND).
        
        Args:
            *expressions: Filter expressions to add
            
        Returns:
            QueryBuilder instance for chaining
        """
        self._filters.extend(expressions)
        return self
    
    def filter_by(self, **kwargs) -> 'QueryBuilder':
        """
        Add simple equality filters.
        
        Args:
            **kwargs: Field name and value pairs
            
        Returns:
            QueryBuilder instance for chaining
        """
        for field, value in kwargs.items():
            self._filters.append(FilterExpression.eq(field, value))
        return self
    
    def or_filter(self, *expressions: FilterExpression) -> 'QueryBuilder':
        """
        Add OR group of filter expressions.
        
        Args:
            *expressions: Filter expressions to combine with OR
            
        Returns:
            QueryBuilder instance for chaining
        """
        if expressions:
            self._or_groups.append(list(expressions))
        return self
    
    def order_by(self, field: str, desc: bool = False) -> 'QueryBuilder':
        """
        Add ordering to the query.
        
        Args:
            field: Field name to order by
            desc: Whether to order in descending order
            
        Returns:
            QueryBuilder instance for chaining
        """
        self._order_by.append((field, desc))
        return self
    
    def order_by_desc(self, field: str) -> 'QueryBuilder':
        """Add descending order to the query."""
        return self.order_by(field, desc=True)
    
    def order_by_asc(self, field: str) -> 'QueryBuilder':
        """Add ascending order to the query."""
        return self.order_by(field, desc=False)
    
    def limit(self, count: int) -> 'QueryBuilder':
        """
        Set limit for the query.
        
        Args:
            count: Maximum number of results
            
        Returns:
            QueryBuilder instance for chaining
        """
        self._limit = count
        return self
    
    def offset(self, count: int) -> 'QueryBuilder':
        """
        Set offset for the query.
        
        Args:
            count: Number of results to skip
            
        Returns:
            QueryBuilder instance for chaining
        """
        self._offset = count
        return self
    
    def page(self, page_number: int, page_size: int) -> 'QueryBuilder':
        """
        Set pagination parameters.
        
        Args:
            page_number: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            QueryBuilder instance for chaining
        """
        self._offset = (page_number - 1) * page_size
        self._limit = page_size
        return self
    
    def distinct(self) -> 'QueryBuilder':
        """
        Make the query return distinct results.
        
        Returns:
            QueryBuilder instance for chaining
        """
        self._distinct = True
        return self
    
    def group_by(self, *fields: str) -> 'QueryBuilder':
        """
        Add GROUP BY fields.
        
        Args:
            *fields: Field names to group by
            
        Returns:
            QueryBuilder instance for chaining
        """
        self._group_by.extend(fields)
        return self
    
    def having(self, *expressions: FilterExpression) -> 'QueryBuilder':
        """
        Add HAVING conditions.
        
        Args:
            *expressions: Filter expressions for HAVING clause
            
        Returns:
            QueryBuilder instance for chaining
        """
        self._having.extend(expressions)
        return self
    
    def _build_query(self) -> Query:
        """Build the SQLAlchemy query object."""
        query = self.session.query(self.model_class)
        
        # Apply DISTINCT
        if self._distinct:
            query = query.distinct()
        
        # Apply filters (AND conditions)
        for filter_expr in self._filters:
            query = query.filter(filter_expr.to_sqlalchemy(self.model_class))
        
        # Apply OR groups
        for or_group in self._or_groups:
            if or_group:
                or_conditions = [
                    expr.to_sqlalchemy(self.model_class) for expr in or_group
                ]
                query = query.filter(or_(*or_conditions))
        
        # Apply GROUP BY
        for field in self._group_by:
            if hasattr(self.model_class, field):
                query = query.group_by(getattr(self.model_class, field))
        
        # Apply HAVING
        for having_expr in self._having:
            query = query.having(having_expr.to_sqlalchemy(self.model_class))
        
        # Apply ORDER BY
        for field, desc_order in self._order_by:
            if hasattr(self.model_class, field):
                order_field = getattr(self.model_class, field)
                if desc_order:
                    query = query.order_by(desc(order_field))
                else:
                    query = query.order_by(asc(order_field))
        
        # Apply OFFSET and LIMIT
        if self._offset > 0:
            query = query.offset(self._offset)
        if self._limit:
            query = query.limit(self._limit)
        
        return query
    
    def all(self) -> List[BaseModel]:
        """Execute query and return all results."""
        return self._build_query().all()
    
    def first(self) -> Optional[BaseModel]:
        """Execute query and return first result."""
        return self._build_query().first()
    
    def one(self) -> BaseModel:
        """Execute query and return exactly one result (raises if 0 or >1)."""
        return self._build_query().one()
    
    def one_or_none(self) -> Optional[BaseModel]:
        """Execute query and return one result or None (raises if >1)."""
        return self._build_query().one_or_none()
    
    def count(self) -> int:
        """Get count of results without executing full query."""
        # Build query without limit/offset for accurate count
        query = self.session.query(func.count(self.model_class.id))
        
        # Apply filters
        for filter_expr in self._filters:
            query = query.filter(filter_expr.to_sqlalchemy(self.model_class))
        
        # Apply OR groups
        for or_group in self._or_groups:
            if or_group:
                or_conditions = [
                    expr.to_sqlalchemy(self.model_class) for expr in or_group
                ]
                query = query.filter(or_(*or_conditions))
        
        return query.scalar() or 0
    
    def exists(self) -> bool:
        """Check if any results exist."""
        return self.session.query(
            self._build_query().exists()
        ).scalar()
    
    def paginate(self, page: int, per_page: int) -> Dict[str, Any]:
        """
        Execute paginated query and return pagination info.
        
        Args:
            page: Page number (1-based)
            per_page: Items per page
            
        Returns:
            Dictionary with pagination information
        """
        # Get total count
        total = self.count()
        
        # Calculate pagination
        total_pages = (total + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        # Get items for current page
        items = self.page(page, per_page).all()
        
        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'has_prev': has_prev,
            'has_next': has_next,
            'prev_page': page - 1 if has_prev else None,
            'next_page': page + 1 if has_next else None
        }
    
    def to_sql(self) -> str:
        """Get the SQL query string (for debugging)."""
        return str(self._build_query().statement.compile(compile_kwargs={"literal_binds": True}))
    
    def clone(self) -> 'QueryBuilder':
        """Create a copy of this query builder."""
        new_builder = QueryBuilder(self.session, self.model_class)
        new_builder._filters = self._filters.copy()
        new_builder._or_groups = [group.copy() for group in self._or_groups]
        new_builder._order_by = self._order_by.copy()
        new_builder._limit = self._limit
        new_builder._offset = self._offset
        new_builder._group_by = self._group_by.copy()
        new_builder._having = self._having.copy()
        new_builder._distinct = self._distinct
        return new_builder
    
    def reset(self) -> 'QueryBuilder':
        """Reset all query conditions."""
        self._filters.clear()
        self._or_groups.clear()
        self._order_by.clear()
        self._limit = None
        self._offset = 0
        self._group_by.clear()
        self._having.clear()
        self._distinct = False
        return self


def create_query_builder(session: Session, model_class: Type[BaseModel]) -> QueryBuilder:
    """
    Create a new query builder instance.
    
    Args:
        session: Database session
        model_class: Model class to query
        
    Returns:
        QueryBuilder instance
    """
    return QueryBuilder(session, model_class)