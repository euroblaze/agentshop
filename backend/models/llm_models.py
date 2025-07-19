from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.orm.base_model import BaseModel


class LLMRequest(BaseModel):
    """Model for storing LLM requests"""
    __tablename__ = 'llm_requests'
    
    # Request identification
    session_id = Column(String(255), nullable=True, index=True)  # For grouping related requests
    user_id = Column(Integer, ForeignKey('customers.id'), nullable=True, index=True)
    request_type = Column(String(50), nullable=False, index=True)  # 'chat', 'generation', 'comparison', etc.
    
    # LLM configuration
    provider = Column(String(50), nullable=False, index=True)
    model = Column(String(100), nullable=False)
    prompt = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=True)
    context = Column(JSON, nullable=True)  # Additional context data
    
    # Generation parameters
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=1000)
    top_p = Column(Float, default=1.0)
    stream = Column(Boolean, default=False)
    
    # Request metadata
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    user_agent = Column(String(500), nullable=True)
    
    # Status and timing
    status = Column(String(20), default='pending', index=True)  # pending, processing, completed, failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Cost tracking
    estimated_cost = Column(Float, default=0.0)
    actual_cost = Column(Float, default=0.0)
    
    # Relationships
    response = relationship("LLMResponse", back_populates="request", uselist=False)
    customer = relationship("Customer", back_populates="llm_requests", foreign_keys=[user_id])


class LLMResponse(BaseModel):
    """Model for storing LLM responses"""
    __tablename__ = 'llm_responses'
    
    # Link to request
    request_id = Column(Integer, ForeignKey('llm_requests.id'), nullable=False, index=True)
    
    # Response content
    content = Column(Text, nullable=False)
    finish_reason = Column(String(50), nullable=True)
    
    # Usage statistics
    tokens_used = Column(Integer, default=0)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    processing_time_ms = Column(Integer, default=0)
    
    # Cost information
    cost = Column(Float, default=0.0)
    cached = Column(Boolean, default=False)
    
    # Response metadata
    metadata = Column(JSON, nullable=True)
    
    # Quality metrics
    response_length = Column(Integer, default=0)
    
    # Relationships
    request = relationship("LLMRequest", back_populates="response")


class LLMConversation(BaseModel):
    """Model for storing conversation threads"""
    __tablename__ = 'llm_conversations'
    
    # Conversation identification
    session_id = Column(String(255), nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey('customers.id'), nullable=True, index=True)
    title = Column(String(200), nullable=True)
    
    # Conversation settings
    default_provider = Column(String(50), nullable=True)
    default_model = Column(String(100), nullable=True)
    system_prompt = Column(Text, nullable=True)
    
    # Conversation metadata
    message_count = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    last_activity = Column(DateTime, default=func.now())
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="llm_conversations", foreign_keys=[user_id])
    messages = relationship("LLMConversationMessage", back_populates="conversation", cascade="all, delete-orphan")


class LLMConversationMessage(BaseModel):
    """Model for storing individual messages in conversations"""
    __tablename__ = 'llm_conversation_messages'
    
    # Link to conversation
    conversation_id = Column(Integer, ForeignKey('llm_conversations.id'), nullable=False, index=True)
    
    # Message content
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    
    # Message metadata
    message_order = Column(Integer, nullable=False)  # Order within conversation
    llm_request_id = Column(Integer, ForeignKey('llm_requests.id'), nullable=True)  # For assistant messages
    
    # Message statistics (for assistant messages)
    tokens_used = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    provider = Column(String(50), nullable=True)
    model = Column(String(100), nullable=True)
    
    # Relationships
    conversation = relationship("LLMConversation", back_populates="messages")
    llm_request = relationship("LLMRequest", foreign_keys=[llm_request_id])


class LLMUsageStats(BaseModel):
    """Model for tracking LLM usage statistics"""
    __tablename__ = 'llm_usage_stats'
    
    # Time period
    date = Column(DateTime, nullable=False, index=True)
    period_type = Column(String(10), nullable=False, index=True)  # 'hour', 'day', 'month'
    
    # Provider/model breakdown
    provider = Column(String(50), nullable=False, index=True)
    model = Column(String(100), nullable=False, index=True)
    
    # Usage metrics
    request_count = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    
    # Token usage
    total_tokens = Column(Integer, default=0)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    
    # Cost metrics
    total_cost = Column(Float, default=0.0)
    average_cost_per_request = Column(Float, default=0.0)
    
    # Performance metrics
    average_response_time_ms = Column(Integer, default=0)
    cache_hit_rate = Column(Float, default=0.0)
    
    # User metrics
    unique_users = Column(Integer, default=0)
    unique_sessions = Column(Integer, default=0)


class LLMProviderStatus(BaseModel):
    """Model for tracking provider health and status"""
    __tablename__ = 'llm_provider_status'
    
    # Provider information
    provider = Column(String(50), nullable=False, unique=True, index=True)
    
    # Status information
    is_enabled = Column(Boolean, default=False)
    is_healthy = Column(Boolean, default=False)
    last_health_check = Column(DateTime, nullable=True)
    
    # Configuration
    api_key_configured = Column(Boolean, default=False)
    default_model = Column(String(100), nullable=True)
    
    # Rate limiting and quotas
    rate_limit_rpm = Column(Integer, default=60)
    daily_cost_limit = Column(Float, default=10.0)
    current_daily_cost = Column(Float, default=0.0)
    
    # Performance metrics
    average_response_time_ms = Column(Integer, default=0)
    error_rate = Column(Float, default=0.0)
    uptime_percentage = Column(Float, default=100.0)
    
    # Error tracking
    last_error = Column(Text, nullable=True)
    last_error_time = Column(DateTime, nullable=True)
    consecutive_errors = Column(Integer, default=0)