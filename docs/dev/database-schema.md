# Database Schema

Complete database schema documentation for AgentShop's simplified architecture.

## Overview

AgentShop uses SQLAlchemy ORM with a unified schema supporting both LLM operations and e-commerce functionality. The schema is organized into logical domains but stored in a single database for simplicity.

## Core Architecture

### Base Model

All models inherit from `BaseModel` in `/core/orm/base_model.py`:

```python
class BaseModel(Base):
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
```

### Available Mixins

- **TimestampMixin** - Adds created_at/updated_at (included in BaseModel)
- **SoftDeleteMixin** - Adds deleted_at/is_deleted fields
- **AuditMixin** - Adds created_by/updated_by tracking
- **VersionMixin** - Adds version field for optimistic locking

## LLM Domain Models

### LLMRequest

Tracks all LLM API requests for analytics and billing.

```python
class LLMRequest(BaseModel):
    __tablename__ = 'llm_requests'
    
    # Request identification
    request_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    
    # Provider information
    provider = Column(String(50), nullable=False, index=True)
    model = Column(String(100), nullable=False)
    
    # Request content
    prompt = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=True)
    max_tokens = Column(Integer, nullable=True)
    temperature = Column(Float, nullable=True)
    
    # Request metadata
    request_type = Column(String(50), default='generate')  # generate, chat, completion
    priority = Column(String(20), default='normal')        # low, normal, high
    
    # Timing and status
    status = Column(String(20), default='pending')         # pending, completed, failed, cancelled
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Error handling
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Relationships
    response = relationship("LLMResponse", back_populates="request", uselist=False)
    conversation_messages = relationship("LLMConversationMessage", back_populates="request")
```

### LLMResponse

Stores LLM responses with usage and cost tracking.

```python
class LLMResponse(BaseModel):
    __tablename__ = 'llm_responses'
    
    # Request reference
    request_id = Column(Integer, ForeignKey('llm_requests.id'), nullable=False, index=True)
    
    # Response content
    content = Column(Text, nullable=False)
    finish_reason = Column(String(50), nullable=True)      # stop, length, content_filter
    
    # Token usage
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    
    # Performance metrics
    response_time = Column(Float, nullable=True)           # Response time in seconds
    queue_time = Column(Float, nullable=True)              # Time spent in queue
    processing_time = Column(Float, nullable=True)         # Actual processing time
    
    # Cost tracking
    cost = Column(Numeric(10, 6), nullable=True)           # Cost in USD
    cost_currency = Column(String(3), default='USD')
    
    # Quality metrics
    confidence_score = Column(Float, nullable=True)        # Provider confidence (if available)
    safety_rating = Column(String(20), nullable=True)      # safe, flagged, blocked
    
    # Caching
    cached = Column(Boolean, default=False)                # Was this response cached?
    cache_key = Column(String(255), nullable=True, index=True)
    
    # Relationships
    request = relationship("LLMRequest", back_populates="response")
```

### LLMConversation

Manages chat conversation sessions.

```python
class LLMConversation(BaseModel):
    __tablename__ = 'llm_conversations'
    
    # Conversation identification
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    
    # Conversation metadata
    title = Column(String(255), nullable=True)             # Auto-generated or user-set
    provider = Column(String(50), nullable=False)          # Primary provider for conversation
    model = Column(String(100), nullable=False)            # Primary model for conversation
    
    # Configuration
    system_prompt = Column(Text, nullable=True)            # Conversation system prompt
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=150)
    
    # Status and metadata
    status = Column(String(20), default='active')          # active, archived, deleted
    message_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Numeric(10, 6), default=0)
    
    # Timestamps
    last_message_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)
    
    # Relationships
    messages = relationship("LLMConversationMessage", back_populates="conversation", 
                          cascade="all, delete-orphan", order_by="LLMConversationMessage.created_at")
```

### LLMConversationMessage

Individual messages within conversations.

```python
class LLMConversationMessage(BaseModel):
    __tablename__ = 'llm_conversation_messages'
    
    # Conversation reference
    conversation_id = Column(Integer, ForeignKey('llm_conversations.id'), nullable=False, index=True)
    request_id = Column(Integer, ForeignKey('llm_requests.id'), nullable=True, index=True)
    
    # Message content
    role = Column(String(20), nullable=False)              # user, assistant, system
    content = Column(Text, nullable=False)
    
    # Message metadata
    sequence_number = Column(Integer, nullable=False)      # Order within conversation
    message_type = Column(String(30), default='text')     # text, image, file, etc.
    
    # Processing info
    provider = Column(String(50), nullable=True)           # Provider that generated response
    model = Column(String(100), nullable=True)             # Model that generated response
    tokens = Column(Integer, nullable=True)
    cost = Column(Numeric(10, 6), nullable=True)
    
    # Message status
    status = Column(String(20), default='sent')            # sent, delivered, read, failed
    edited = Column(Boolean, default=False)
    edited_at = Column(DateTime, nullable=True)
    
    # Relationships
    conversation = relationship("LLMConversation", back_populates="messages")
    request = relationship("LLMRequest", back_populates="conversation_messages")
```

### LLMUsageStats

Aggregated usage statistics for analytics.

```python
class LLMUsageStats(BaseModel):
    __tablename__ = 'llm_usage_stats'
    
    # Time period
    date = Column(Date, nullable=False, index=True)
    hour = Column(Integer, nullable=True, index=True)      # For hourly stats (0-23)
    
    # Aggregation keys
    provider = Column(String(50), nullable=False, index=True)
    model = Column(String(100), nullable=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    
    # Usage metrics
    request_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    
    # Token usage
    total_tokens = Column(Integer, default=0)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    
    # Cost metrics
    total_cost = Column(Numeric(10, 6), default=0)
    average_cost_per_request = Column(Numeric(10, 6), default=0)
    
    # Performance metrics
    average_response_time = Column(Float, default=0)
    min_response_time = Column(Float, nullable=True)
    max_response_time = Column(Float, nullable=True)
    
    # Cache metrics
    cache_hit_count = Column(Integer, default=0)
    cache_miss_count = Column(Integer, default=0)
    
    # Unique constraints
    __table_args__ = (
        UniqueConstraint('date', 'hour', 'provider', 'model', 'user_id', 
                        name='unique_usage_stat'),
    )
```

### LLMProviderStatus

Provider health and configuration status.

```python
class LLMProviderStatus(BaseModel):
    __tablename__ = 'llm_provider_status'
    
    # Provider identification
    provider = Column(String(50), unique=True, nullable=False, index=True)
    
    # Status information
    status = Column(String(20), default='unknown')         # healthy, degraded, down, unknown
    enabled = Column(Boolean, default=True)
    
    # Health metrics
    last_check_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_error_at = Column(DateTime, nullable=True)
    
    # Performance metrics
    average_response_time = Column(Float, nullable=True)   # Last 24h average
    success_rate = Column(Float, nullable=True)            # Last 24h success rate (0-100)
    
    # Error tracking
    consecutive_failures = Column(Integer, default=0)
    last_error_message = Column(Text, nullable=True)
    last_error_code = Column(String(50), nullable=True)
    
    # Configuration
    priority = Column(Integer, default=100)                # Load balancing priority
    rate_limit = Column(Integer, nullable=True)            # Requests per minute limit
    
    # Maintenance
    maintenance_mode = Column(Boolean, default=False)
    maintenance_message = Column(Text, nullable=True)
    maintenance_until = Column(DateTime, nullable=True)
```

## E-commerce Domain Models

### Product

Core product information for the marketplace.

```python
class Product(BaseModel, SoftDeleteMixin):
    __tablename__ = 'products'
    
    # Basic information
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    
    # Content
    short_description = Column(Text, nullable=True)
    full_description = Column(Text, nullable=True)
    
    # Categorization
    category_id = Column(Integer, ForeignKey('product_categories.id'), nullable=True, index=True)
    tags = Column(Text, nullable=True)                     # JSON array of tags
    
    # Pricing
    price = Column(Numeric(10, 2), nullable=False)
    price_type = Column(String(20), default='fixed')       # fixed, inquiry, free, subscription
    sale_price = Column(Numeric(10, 2), nullable=True)
    sale_start = Column(DateTime, nullable=True)
    sale_end = Column(DateTime, nullable=True)
    
    # Status and visibility
    status = Column(String(20), default='draft')           # draft, active, inactive, archived
    featured = Column(Boolean, default=False)
    
    # Media
    featured_image = Column(String(500), nullable=True)
    gallery_images = Column(Text, nullable=True)           # JSON array of image URLs
    demo_video_url = Column(String(500), nullable=True)
    
    # Metadata
    sku = Column(String(100), unique=True, nullable=True, index=True)
    weight = Column(Float, nullable=True)                  # For shipping calculations
    dimensions = Column(Text, nullable=True)               # JSON object with dimensions
    
    # SEO
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    meta_keywords = Column(Text, nullable=True)
    
    # Stats
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    rating_average = Column(Float, nullable=True)
    rating_count = Column(Integer, default=0)
    
    # Digital product specifics
    download_files = Column(Text, nullable=True)           # JSON array of file info
    license_type = Column(String(50), nullable=True)       # personal, commercial, enterprise
    system_requirements = Column(Text, nullable=True)      # JSON object
    
    # AI/LLM specific
    supported_providers = Column(Text, nullable=True)      # JSON array of supported LLM providers
    model_requirements = Column(Text, nullable=True)       # JSON object with model requirements
    
    # Relationships
    category = relationship("ProductCategory", back_populates="products")
    reviews = relationship("ProductReview", back_populates="product", cascade="all, delete-orphan")
    inquiries = relationship("ProductInquiry", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")
```

### ProductCategory

Product categorization system.

```python
class ProductCategory(BaseModel):
    __tablename__ = 'product_categories'
    
    # Basic information
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Hierarchy
    parent_id = Column(Integer, ForeignKey('product_categories.id'), nullable=True, index=True)
    sort_order = Column(Integer, default=0)
    
    # Display
    icon = Column(String(255), nullable=True)
    color = Column(String(7), nullable=True)               # Hex color code
    featured = Column(Boolean, default=False)
    
    # SEO
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    
    # Status
    active = Column(Boolean, default=True)
    
    # Relationships
    parent = relationship("ProductCategory", remote_side="ProductCategory.id", back_populates="children")
    children = relationship("ProductCategory", back_populates="parent", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="category")
```

### Customer

Customer account management.

```python
class Customer(BaseModel, SoftDeleteMixin):
    __tablename__ = 'customers'
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255), nullable=True)
    
    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    
    # Address information
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)
    
    # Password reset
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    
    # Preferences
    email_marketing = Column(Boolean, default=False)
    sms_marketing = Column(Boolean, default=False)
    newsletter = Column(Boolean, default=False)
    
    # Customer metadata
    registration_ip = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    referral_source = Column(String(200), nullable=True)
    
    # Stats
    total_orders = Column(Integer, default=0)
    total_spent = Column(Numeric(10, 2), default=0)
    average_order_value = Column(Numeric(10, 2), default=0)
    
    # Relationships
    sessions = relationship("CustomerSession", back_populates="customer", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="customer")
    reviews = relationship("ProductReview", back_populates="customer")
    inquiries = relationship("ProductInquiry", back_populates="customer")
    support_requests = relationship("SupportRequest", back_populates="customer")
```

### Order

Order processing and management.

```python
class Order(BaseModel):
    __tablename__ = 'orders'
    
    # Order identification
    order_number = Column(String(100), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False, index=True)
    
    # Order status
    status = Column(String(20), default='pending')         # pending, processing, completed, cancelled, refunded
    payment_status = Column(String(20), default='pending') # pending, paid, failed, refunded
    
    # Amounts
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0)
    shipping_amount = Column(Numeric(10, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    total_amount = Column(Numeric(10, 2), nullable=False)
    
    # Currency
    currency = Column(String(3), default='USD')
    
    # Billing information
    billing_first_name = Column(String(100), nullable=False)
    billing_last_name = Column(String(100), nullable=False)
    billing_email = Column(String(255), nullable=False)
    billing_phone = Column(String(20), nullable=True)
    billing_address_line1 = Column(String(255), nullable=False)
    billing_address_line2 = Column(String(255), nullable=True)
    billing_city = Column(String(100), nullable=False)
    billing_state = Column(String(100), nullable=False)
    billing_postal_code = Column(String(20), nullable=False)
    billing_country = Column(String(100), nullable=False)
    
    # Shipping information (for physical goods)
    shipping_first_name = Column(String(100), nullable=True)
    shipping_last_name = Column(String(100), nullable=True)
    shipping_address_line1 = Column(String(255), nullable=True)
    shipping_address_line2 = Column(String(255), nullable=True)
    shipping_city = Column(String(100), nullable=True)
    shipping_state = Column(String(100), nullable=True)
    shipping_postal_code = Column(String(20), nullable=True)
    shipping_country = Column(String(100), nullable=True)
    
    # Payment information
    payment_method = Column(String(50), nullable=True)     # credit_card, paypal, crypto, etc.
    payment_processor = Column(String(50), nullable=True)  # stripe, paypal, etc.
    payment_transaction_id = Column(String(255), nullable=True)
    
    # Order metadata
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    source = Column(String(50), default='web')             # web, api, admin, etc.
    
    # Timestamps
    processed_at = Column(DateTime, nullable=True)
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    support_requests = relationship("SupportRequest", back_populates="order")
```

### OrderItem

Individual items within an order.

```python
class OrderItem(BaseModel):
    __tablename__ = 'order_items'
    
    # References
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    
    # Item details
    product_name = Column(String(255), nullable=False)     # Snapshot at time of order
    product_sku = Column(String(100), nullable=True)       # Snapshot at time of order
    
    # Pricing
    unit_price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    # Digital delivery
    license_key = Column(String(255), nullable=True)
    download_url = Column(String(500), nullable=True)
    download_expires_at = Column(DateTime, nullable=True)
    download_count = Column(Integer, default=0)
    max_downloads = Column(Integer, default=5)
    
    # Status
    status = Column(String(20), default='pending')         # pending, delivered, expired
    delivered_at = Column(DateTime, nullable=True)
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
```

## Admin Domain Models

### AdminUser

Administrative user accounts.

```python
class AdminUser(BaseModel):
    __tablename__ = 'admin_users'
    
    # Authentication
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    
    # Permissions
    is_superuser = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    permissions = Column(Text, nullable=True)              # JSON array of permissions
    
    # Login tracking
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    # Metadata
    notes = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)
    
    # Relationships
    sessions = relationship("AdminSession", back_populates="admin_user", cascade="all, delete-orphan")
```

### ConfigSetting

System configuration storage.

```python
class ConfigSetting(BaseModel):
    __tablename__ = 'config_settings'
    
    # Setting identification
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    
    # Metadata
    description = Column(Text, nullable=True)
    data_type = Column(String(20), default='string')       # string, integer, float, boolean, json
    category = Column(String(100), default='general', index=True)
    
    # Security
    is_sensitive = Column(Boolean, default=False)          # Hide value in admin interface
    encrypted = Column(Boolean, default=False)             # Is value encrypted?
    
    # Validation
    validation_rules = Column(Text, nullable=True)         # JSON validation rules
    default_value = Column(Text, nullable=True)
    
    # Status
    active = Column(Boolean, default=True)
    read_only = Column(Boolean, default=False)
```

## Indexes

### Performance Indexes

```sql
-- LLM request lookup
CREATE INDEX idx_llm_requests_user_provider ON llm_requests(user_id, provider);
CREATE INDEX idx_llm_requests_session ON llm_requests(session_id);
CREATE INDEX idx_llm_requests_status_created ON llm_requests(status, created_at);

-- Analytics queries
CREATE INDEX idx_llm_usage_stats_date_provider ON llm_usage_stats(date, provider);
CREATE INDEX idx_llm_usage_stats_user_date ON llm_usage_stats(user_id, date);

-- Product searches
CREATE INDEX idx_products_category_status ON products(category_id, status);
CREATE INDEX idx_products_featured_status ON products(featured, status);

-- Order management
CREATE INDEX idx_orders_customer_status ON orders(customer_id, status);
CREATE INDEX idx_orders_status_created ON orders(status, created_at);

-- Customer lookup
CREATE INDEX idx_customers_email_active ON customers(email, is_active);
```

### Full-Text Search

```sql
-- Product search (PostgreSQL)
CREATE INDEX idx_products_search ON products USING gin(to_tsvector('english', name || ' ' || coalesce(short_description, '')));

-- For SQLite, use FTS virtual table
CREATE VIRTUAL TABLE products_fts USING fts5(name, short_description, content='products', content_rowid='id');
```

## Migration Notes

### Database Initialization

The database is automatically initialized on first run using SQLAlchemy's `create_all()`:

```python
from core.orm.database import create_all_tables
create_all_tables()
```

### Sample Data

For development, sample data can be loaded:

```python
from backend.scripts.load_sample_data import load_sample_data
load_sample_data()
```

### Backup and Restore

**SQLite (Development):**
```bash
# Backup
cp agentshop.db agentshop_backup.db

# Restore
cp agentshop_backup.db agentshop.db
```

**PostgreSQL (Production):**
```bash
# Backup
pg_dump agentshop > backup.sql

# Restore
psql agentshop < backup.sql
```

## Performance Considerations

### Query Optimization

1. **Use appropriate indexes** for common query patterns
2. **Eager load relationships** when needed to avoid N+1 queries
3. **Implement pagination** for large result sets
4. **Use database-level aggregations** for analytics

### Scaling Considerations

1. **Read replicas** for analytics queries
2. **Connection pooling** for high concurrency
3. **Caching layer** (Redis) for frequently accessed data
4. **Archive old data** to keep tables manageable

---

**For implementation details, see the [Core ORM Documentation](../core/orm/).**