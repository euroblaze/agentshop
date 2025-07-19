-- AgentShop Database Schema
-- This script creates all tables for the AI Agent Marketplace
-- Compatible with PostgreSQL, MySQL, and SQLite (with minor adjustments)

-- =============================================================================
-- CORE CUSTOMER AND USER TABLES
-- =============================================================================

-- Customers table for shop users
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    
    -- Address information
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(50),
    
    -- Account status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    last_login DATETIME,
    
    -- Preferences
    marketing_emails BOOLEAN DEFAULT TRUE,
    newsletter BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Admin users for backend management
CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'admin',
    is_active BOOLEAN DEFAULT TRUE,
    last_login DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Session management for customers
CREATE TABLE IF NOT EXISTS customer_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at DATETIME NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

-- Session management for admin users
CREATE TABLE IF NOT EXISTS admin_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at DATETIME NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES admin_users(id) ON DELETE CASCADE
);

-- =============================================================================
-- PRODUCT MANAGEMENT TABLES
-- =============================================================================

-- Products/AI Agents for sale
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    title VARCHAR(300) NOT NULL,
    short_description TEXT,
    full_description TEXT,
    
    -- Pricing
    price INTEGER, -- Price in cents, NULL for quote-based
    price_type VARCHAR(20) DEFAULT 'fixed', -- 'fixed' or 'quote'
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Content
    html_content TEXT,
    readme_link VARCHAR(500),
    download_link VARCHAR(500),
    
    -- Media
    thumbnail_url VARCHAR(500),
    gallery_images TEXT, -- JSON array of image URLs
    
    -- SEO and categorization
    slug VARCHAR(200) UNIQUE,
    category VARCHAR(100),
    tags TEXT, -- JSON array of tags
    meta_title VARCHAR(200),
    meta_description TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    stock_quantity INTEGER,
    
    -- Analytics
    view_count INTEGER DEFAULT 0,
    download_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Product categories
CREATE TABLE IF NOT EXISTS product_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    parent_id INTEGER,
    slug VARCHAR(200) UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES product_categories(id)
);

-- Product reviews (thumbs up system)
CREATE TABLE IF NOT EXISTS product_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    customer_id INTEGER,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    thumbs_up BOOLEAN DEFAULT FALSE,
    review_text TEXT,
    is_verified_purchase BOOLEAN DEFAULT FALSE,
    is_approved BOOLEAN DEFAULT TRUE,
    ip_address VARCHAR(45),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
);

-- =============================================================================
-- ORDER AND PAYMENT TABLES
-- =============================================================================

-- Orders
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Order totals
    subtotal INTEGER NOT NULL, -- Amount in cents
    tax_amount INTEGER DEFAULT 0,
    shipping_amount INTEGER DEFAULT 0,
    total_amount INTEGER NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, cancelled, refunded
    
    -- Payment information
    payment_processor VARCHAR(20), -- 'stripe', 'paypal'
    payment_status VARCHAR(20) DEFAULT 'pending',
    transaction_id VARCHAR(255),
    payment_method VARCHAR(50),
    
    -- Shipping information
    shipping_first_name VARCHAR(100),
    shipping_last_name VARCHAR(100),
    shipping_address_line1 VARCHAR(255),
    shipping_address_line2 VARCHAR(255),
    shipping_city VARCHAR(100),
    shipping_state VARCHAR(50),
    shipping_postal_code VARCHAR(20),
    shipping_country VARCHAR(50),
    
    -- Timestamps
    ordered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    shipped_at DATETIME,
    delivered_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Order items
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price INTEGER NOT NULL, -- Price in cents at time of order
    total_price INTEGER NOT NULL,
    
    -- Product snapshot at time of order
    product_name VARCHAR(200),
    product_description TEXT,
    download_link VARCHAR(500),
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- =============================================================================
-- LLM INTEGRATION TABLES
-- =============================================================================

-- LLM Requests
CREATE TABLE IF NOT EXISTS llm_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Request identification
    session_id VARCHAR(255),
    user_id INTEGER,
    request_type VARCHAR(50) NOT NULL, -- 'chat', 'generation', 'comparison', etc.
    
    -- LLM configuration
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    prompt TEXT NOT NULL,
    system_prompt TEXT,
    context TEXT, -- JSON context data
    
    -- Generation parameters
    temperature REAL DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 1000,
    top_p REAL DEFAULT 1.0,
    stream BOOLEAN DEFAULT FALSE,
    
    -- Request metadata
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    -- Status and timing
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    started_at DATETIME,
    completed_at DATETIME,
    
    -- Cost tracking
    estimated_cost REAL DEFAULT 0.0,
    actual_cost REAL DEFAULT 0.0,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES customers(id) ON DELETE SET NULL
);

-- LLM Responses
CREATE TABLE IF NOT EXISTS llm_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    
    -- Response content
    content TEXT NOT NULL,
    finish_reason VARCHAR(50),
    
    -- Usage statistics
    tokens_used INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    processing_time_ms INTEGER DEFAULT 0,
    
    -- Cost information
    cost REAL DEFAULT 0.0,
    cached BOOLEAN DEFAULT FALSE,
    
    -- Response metadata
    metadata TEXT, -- JSON metadata
    response_length INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (request_id) REFERENCES llm_requests(id) ON DELETE CASCADE
);

-- LLM Conversations
CREATE TABLE IF NOT EXISTS llm_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Conversation identification
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER,
    title VARCHAR(200),
    
    -- Conversation settings
    default_provider VARCHAR(50),
    default_model VARCHAR(100),
    system_prompt TEXT,
    
    -- Conversation metadata
    message_count INTEGER DEFAULT 0,
    total_cost REAL DEFAULT 0.0,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES customers(id) ON DELETE SET NULL
);

-- LLM Conversation Messages
CREATE TABLE IF NOT EXISTS llm_conversation_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    
    -- Message content
    role VARCHAR(20) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    
    -- Message metadata
    message_order INTEGER NOT NULL,
    llm_request_id INTEGER,
    
    -- Message statistics (for assistant messages)
    tokens_used INTEGER DEFAULT 0,
    cost REAL DEFAULT 0.0,
    provider VARCHAR(50),
    model VARCHAR(100),
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (conversation_id) REFERENCES llm_conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (llm_request_id) REFERENCES llm_requests(id) ON DELETE SET NULL
);

-- LLM Usage Statistics
CREATE TABLE IF NOT EXISTS llm_usage_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Time period
    date DATETIME NOT NULL,
    period_type VARCHAR(10) NOT NULL, -- 'hour', 'day', 'month'
    
    -- Provider/model breakdown
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    
    -- Usage metrics
    request_count INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    
    -- Token usage
    total_tokens INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    
    -- Cost metrics
    total_cost REAL DEFAULT 0.0,
    average_cost_per_request REAL DEFAULT 0.0,
    
    -- Performance metrics
    average_response_time_ms INTEGER DEFAULT 0,
    cache_hit_rate REAL DEFAULT 0.0,
    
    -- User metrics
    unique_users INTEGER DEFAULT 0,
    unique_sessions INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- LLM Provider Status
CREATE TABLE IF NOT EXISTS llm_provider_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Provider information
    provider VARCHAR(50) UNIQUE NOT NULL,
    
    -- Status information
    is_enabled BOOLEAN DEFAULT FALSE,
    is_healthy BOOLEAN DEFAULT FALSE,
    last_health_check DATETIME,
    
    -- Configuration
    api_key_configured BOOLEAN DEFAULT FALSE,
    default_model VARCHAR(100),
    
    -- Rate limiting and quotas
    rate_limit_rpm INTEGER DEFAULT 60,
    daily_cost_limit REAL DEFAULT 10.0,
    current_daily_cost REAL DEFAULT 0.0,
    
    -- Performance metrics
    average_response_time_ms INTEGER DEFAULT 0,
    error_rate REAL DEFAULT 0.0,
    uptime_percentage REAL DEFAULT 100.0,
    
    -- Error tracking
    last_error TEXT,
    last_error_time DATETIME,
    consecutive_errors INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- SUPPORT AND COMMUNICATION TABLES
-- =============================================================================

-- Support requests
CREATE TABLE IF NOT EXISTS support_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    order_id INTEGER,
    
    -- Request details
    subject VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'open', -- open, in_progress, resolved, closed
    priority VARCHAR(10) DEFAULT 'normal', -- low, normal, high, urgent
    category VARCHAR(50), -- technical, billing, general, etc.
    
    -- Contact information (for non-registered users)
    contact_email VARCHAR(255),
    contact_name VARCHAR(100),
    
    -- Assignment
    assigned_to INTEGER,
    
    -- Timestamps
    resolved_at DATETIME,
    closed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL,
    FOREIGN KEY (assigned_to) REFERENCES admin_users(id) ON DELETE SET NULL
);

-- Support request messages/replies
CREATE TABLE IF NOT EXISTS support_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    support_request_id INTEGER NOT NULL,
    sender_type VARCHAR(20) NOT NULL, -- 'customer', 'admin'
    sender_id INTEGER,
    message TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT FALSE,
    
    -- Attachments
    attachments TEXT, -- JSON array of file URLs
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (support_request_id) REFERENCES support_requests(id) ON DELETE CASCADE
);

-- Product inquiries (ask about product feature)
CREATE TABLE IF NOT EXISTS product_inquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    customer_email VARCHAR(255) NOT NULL,
    customer_name VARCHAR(100),
    question TEXT NOT NULL,
    answer TEXT,
    status VARCHAR(20) DEFAULT 'pending', -- pending, answered, closed
    is_public BOOLEAN DEFAULT FALSE, -- Show in FAQ
    ip_address VARCHAR(45),
    
    -- Timestamps
    answered_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- =============================================================================
-- AUTOMATION AND DATA TABLES
-- =============================================================================

-- Webcrawler jobs and results
CREATE TABLE IF NOT EXISTS webcrawler_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Job configuration
    job_name VARCHAR(200) NOT NULL,
    job_type VARCHAR(50) NOT NULL, -- 'product_research', 'competitor_analysis', 'content_scraping'
    target_url VARCHAR(1000) NOT NULL,
    crawler_config TEXT, -- JSON configuration
    
    -- Scheduling
    schedule_type VARCHAR(20), -- 'once', 'daily', 'weekly', 'monthly'
    cron_expression VARCHAR(100),
    next_run_at DATETIME,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- pending, running, completed, failed, paused
    last_run_at DATETIME,
    last_success_at DATETIME,
    last_error TEXT,
    
    -- Results
    items_scraped INTEGER DEFAULT 0,
    data_file_path VARCHAR(500),
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Scraped data records
CREATE TABLE IF NOT EXISTS scraped_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    
    -- Data identification
    source_url VARCHAR(1000),
    data_type VARCHAR(50), -- 'product', 'review', 'article', 'image'
    title VARCHAR(500),
    
    -- Content
    content TEXT,
    structured_data TEXT, -- JSON structured data
    raw_html TEXT,
    
    -- Metadata
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    content_hash VARCHAR(64), -- For deduplication
    file_path VARCHAR(500), -- If saved to file
    
    -- Processing status
    is_processed BOOLEAN DEFAULT FALSE,
    processed_at DATETIME,
    processing_errors TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (job_id) REFERENCES webcrawler_jobs(id) ON DELETE CASCADE
);

-- Data processing tasks
CREATE TABLE IF NOT EXISTS data_processing_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Task configuration
    task_name VARCHAR(200) NOT NULL,
    task_type VARCHAR(50) NOT NULL, -- 'data_cleaning', 'analysis', 'ml_training', 'export'
    input_source VARCHAR(100), -- 'scraped_data', 'orders', 'llm_responses'
    
    -- Processing configuration
    config TEXT, -- JSON configuration
    filters TEXT, -- JSON filters for data selection
    
    -- Scheduling
    schedule_type VARCHAR(20), -- 'once', 'daily', 'weekly', 'monthly'
    cron_expression VARCHAR(100),
    next_run_at DATETIME,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending',
    last_run_at DATETIME,
    last_success_at DATETIME,
    last_error TEXT,
    
    -- Results
    records_processed INTEGER DEFAULT 0,
    output_file_path VARCHAR(500),
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- CONFIGURATION AND SETTINGS TABLES
-- =============================================================================

-- System configuration
CREATE TABLE IF NOT EXISTS config_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    data_type VARCHAR(20) DEFAULT 'string', -- string, integer, boolean, json
    is_public BOOLEAN DEFAULT FALSE, -- Can be exposed to frontend
    category VARCHAR(50),
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Email templates
CREATE TABLE IF NOT EXISTS email_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    subject VARCHAR(200) NOT NULL,
    html_content TEXT NOT NULL,
    text_content TEXT,
    variables TEXT, -- JSON array of available variables
    category VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- ANALYTICS AND REPORTING TABLES
-- =============================================================================

-- Website analytics
CREATE TABLE IF NOT EXISTS analytics_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Event identification
    event_type VARCHAR(50) NOT NULL, -- 'page_view', 'product_view', 'search', 'purchase'
    event_name VARCHAR(100),
    
    -- User identification
    session_id VARCHAR(255),
    user_id INTEGER,
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    -- Event data
    page_url VARCHAR(1000),
    referrer_url VARCHAR(1000),
    event_data TEXT, -- JSON event data
    
    -- Timestamps
    event_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES customers(id) ON DELETE SET NULL
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Customer indexes
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_active ON customers(is_active);

-- Product indexes
CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_featured ON products(is_featured);
CREATE INDEX IF NOT EXISTS idx_products_slug ON products(slug);

-- Order indexes
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(created_at);

-- LLM indexes
CREATE INDEX IF NOT EXISTS idx_llm_requests_session ON llm_requests(session_id);
CREATE INDEX IF NOT EXISTS idx_llm_requests_user ON llm_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_llm_requests_provider ON llm_requests(provider);
CREATE INDEX IF NOT EXISTS idx_llm_requests_status ON llm_requests(status);
CREATE INDEX IF NOT EXISTS idx_llm_conversations_session ON llm_conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_stats_date ON llm_usage_stats(date, period_type);

-- Support indexes
CREATE INDEX IF NOT EXISTS idx_support_customer ON support_requests(customer_id);
CREATE INDEX IF NOT EXISTS idx_support_status ON support_requests(status);

-- Analytics indexes
CREATE INDEX IF NOT EXISTS idx_analytics_event_type ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics_events(event_timestamp);
CREATE INDEX IF NOT EXISTS idx_analytics_session ON analytics_events(session_id);

-- Webcrawler indexes
CREATE INDEX IF NOT EXISTS idx_webcrawler_status ON webcrawler_jobs(status);
CREATE INDEX IF NOT EXISTS idx_scraped_data_job ON scraped_data(job_id);
CREATE INDEX IF NOT EXISTS idx_scraped_data_processed ON scraped_data(is_processed);

-- =============================================================================
-- INITIAL DATA POPULATION
-- =============================================================================

-- Insert default admin user (password: 'admin123' - change in production!)
INSERT OR IGNORE INTO admin_users (username, email, password_hash, role) VALUES 
('admin', 'admin@agentshop.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewLz1j.mKQ3pI2G6', 'super_admin');

-- Insert default product categories
INSERT OR IGNORE INTO product_categories (name, description, slug, sort_order) VALUES 
('AI Agents', 'Intelligent AI agent software', 'ai-agents', 1),
('Chatbots', 'Conversational AI and chatbot solutions', 'chatbots', 2),
('Automation Tools', 'AI-powered automation and workflow tools', 'automation-tools', 3),
('Data Analysis', 'AI tools for data processing and analysis', 'data-analysis', 4),
('Content Generation', 'AI content creation and writing tools', 'content-generation', 5);

-- Insert default configuration settings
INSERT OR IGNORE INTO config_settings (key, value, description, data_type, is_public, category) VALUES 
('site_name', 'AgentShop', 'Website name', 'string', TRUE, 'general'),
('site_description', 'AI Agent Marketplace', 'Website description', 'string', TRUE, 'general'),
('default_currency', 'USD', 'Default currency for pricing', 'string', TRUE, 'commerce'),
('enable_reviews', 'true', 'Enable product reviews', 'boolean', TRUE, 'features'),
('max_file_upload_size', '10485760', 'Maximum file upload size in bytes', 'integer', FALSE, 'system'),
('smtp_host', 'localhost', 'SMTP server host', 'string', FALSE, 'email'),
('stripe_webhook_secret', '', 'Stripe webhook secret', 'string', FALSE, 'payments'),
('paypal_client_id', '', 'PayPal client ID', 'string', FALSE, 'payments');

-- Insert default email templates
INSERT OR IGNORE INTO email_templates (name, subject, html_content, text_content, category) VALUES 
('order_confirmation', 'Order Confirmation - {{order_number}}', 
 '<h1>Thank you for your order!</h1><p>Order #{{order_number}} has been confirmed.</p><p>Download link: <a href="{{download_link}}">{{product_name}}</a></p>', 
 'Thank you for your order! Order #{{order_number}} has been confirmed. Download link: {{download_link}}', 
 'orders'),
('welcome_customer', 'Welcome to AgentShop!', 
 '<h1>Welcome to AgentShop!</h1><p>Thank you for creating an account. Start exploring our AI agents!</p>', 
 'Welcome to AgentShop! Thank you for creating an account.', 
 'customers'),
('support_ticket_created', 'Support Request Created - {{ticket_id}}', 
 '<h1>Support Request Created</h1><p>We have received your support request #{{ticket_id}}. We will respond soon.</p>', 
 'Support request #{{ticket_id}} has been created. We will respond soon.', 
 'support');

-- Insert LLM provider status records
INSERT OR IGNORE INTO llm_provider_status (provider, is_enabled, is_healthy, api_key_configured) VALUES 
('ollama', FALSE, FALSE, FALSE),
('openai', FALSE, FALSE, FALSE),
('claude', FALSE, FALSE, FALSE),
('perplexity', FALSE, FALSE, FALSE),
('groq', FALSE, FALSE, FALSE);

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Customer order summary view
CREATE VIEW IF NOT EXISTS customer_order_summary AS
SELECT 
    c.id as customer_id,
    c.email,
    c.first_name,
    c.last_name,
    COUNT(o.id) as total_orders,
    SUM(o.total_amount) as total_spent,
    MAX(o.created_at) as last_order_date,
    c.created_at as customer_since
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id AND o.status = 'completed'
GROUP BY c.id, c.email, c.first_name, c.last_name, c.created_at;

-- Product performance view
CREATE VIEW IF NOT EXISTS product_performance AS
SELECT 
    p.id,
    p.name,
    p.price,
    p.view_count,
    COUNT(pr.id) as review_count,
    AVG(CASE WHEN pr.rating > 0 THEN pr.rating END) as avg_rating,
    SUM(CASE WHEN pr.thumbs_up THEN 1 ELSE 0 END) as thumbs_up_count,
    COUNT(oi.id) as times_purchased,
    SUM(oi.total_price) as total_revenue
FROM products p
LEFT JOIN product_reviews pr ON p.id = pr.product_id AND pr.is_approved = TRUE
LEFT JOIN order_items oi ON p.id = oi.product_id
GROUP BY p.id, p.name, p.price, p.view_count;

-- LLM usage summary view
CREATE VIEW IF NOT EXISTS llm_daily_summary AS
SELECT 
    DATE(created_at) as date,
    provider,
    COUNT(*) as total_requests,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_requests,
    SUM(actual_cost) as total_cost,
    AVG(CASE WHEN completed_at IS NOT NULL AND started_at IS NOT NULL 
        THEN (julianday(completed_at) - julianday(started_at)) * 86400000 
        ELSE NULL END) as avg_response_time_ms
FROM llm_requests
WHERE created_at >= date('now', '-30 days')
GROUP BY DATE(created_at), provider
ORDER BY date DESC, provider;

-- =============================================================================
-- TRIGGERS FOR DATA INTEGRITY
-- =============================================================================

-- Update timestamps trigger for customers
CREATE TRIGGER IF NOT EXISTS update_customers_timestamp 
AFTER UPDATE ON customers
BEGIN
    UPDATE customers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update timestamps trigger for products
CREATE TRIGGER IF NOT EXISTS update_products_timestamp 
AFTER UPDATE ON products
BEGIN
    UPDATE products SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update conversation stats when message is added
CREATE TRIGGER IF NOT EXISTS update_conversation_stats 
AFTER INSERT ON llm_conversation_messages
BEGIN
    UPDATE llm_conversations 
    SET message_count = message_count + 1,
        last_activity = CURRENT_TIMESTAMP,
        total_cost = total_cost + COALESCE(NEW.cost, 0)
    WHERE id = NEW.conversation_id;
END;

-- =============================================================================
-- COMPLETION MESSAGE
-- =============================================================================

-- Database schema creation completed
-- Run this script to create all tables for AgentShop
-- Remember to:
-- 1. Change default admin password
-- 2. Configure SMTP settings
-- 3. Set up payment gateway credentials
-- 4. Enable desired LLM providers
-- 5. Customize configuration settings