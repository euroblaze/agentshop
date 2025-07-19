# API Reference

Complete API documentation for AgentShop's simplified architecture.

## Base URL

- **Development:** `http://localhost:5000`
- **Production:** `https://your-domain.com`

## Authentication

Most endpoints require authentication via JWT tokens.

```http
Authorization: Bearer <jwt_token>
```

## Core LLM Operations

### List Available Providers

```http
GET /api/llm/providers
```

**Response:**
```json
{
  "providers": [
    {
      "name": "openai",
      "enabled": true,
      "models": ["gpt-4", "gpt-3.5-turbo"],
      "status": "healthy"
    },
    {
      "name": "claude",
      "enabled": true,
      "models": ["claude-3-opus", "claude-3-sonnet"],
      "status": "healthy"
    }
  ]
}
```

### Get Models for Provider

```http
GET /api/llm/models/{provider}
```

**Parameters:**
- `provider` (string): Provider name (openai, claude, groq, etc.)

**Response:**
```json
{
  "provider": "openai",
  "models": [
    {
      "id": "gpt-4",
      "name": "GPT-4",
      "context_length": 8192,
      "cost_per_token": 0.00003
    },
    {
      "id": "gpt-3.5-turbo",
      "name": "GPT-3.5 Turbo",
      "context_length": 4096,
      "cost_per_token": 0.000002
    }
  ]
}
```

### Generate Text

```http
POST /api/llm/generate
```

**Request Body:**
```json
{
  "prompt": "Explain quantum computing",
  "provider": "openai",
  "model": "gpt-3.5-turbo",
  "user_id": 123,
  "session_id": "session-abc-123",
  "max_tokens": 150,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "id": "req-abc-123",
  "content": "Quantum computing is a type of computation...",
  "provider": "openai",
  "model": "gpt-3.5-turbo",
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 89,
    "total_tokens": 101
  },
  "cost": 0.000202,
  "response_time": 1.23
}
```

## Chat Operations

### Send Chat Message

```http
POST /api/llm/chat/message
```

**Request Body:**
```json
{
  "message": "Hello, how can you help me?",
  "session_id": "chat-session-1",
  "provider": "claude",
  "user_id": 123
}
```

**Response:**
```json
{
  "id": "msg-abc-123",
  "content": "Hello! I'm an AI assistant...",
  "session_id": "chat-session-1",
  "provider": "claude",
  "model": "claude-3-haiku",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Get Conversation History

```http
GET /api/llm/chat/history/{session_id}
```

**Parameters:**
- `session_id` (string): Chat session identifier
- `limit` (int, optional): Maximum messages to return (default: 50)
- `offset` (int, optional): Number of messages to skip (default: 0)

**Response:**
```json
{
  "session_id": "chat-session-1",
  "messages": [
    {
      "id": "msg-1",
      "role": "user",
      "content": "Hello",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "id": "msg-2", 
      "role": "assistant",
      "content": "Hello! How can I help?",
      "timestamp": "2024-01-15T10:30:05Z"
    }
  ],
  "total_messages": 2
}
```

### Compare Providers

```http
POST /api/llm/chat/compare
```

**Request Body:**
```json
{
  "prompt": "Write a haiku about AI",
  "providers": ["openai", "claude", "groq"],
  "user_id": 123
}
```

**Response:**
```json
{
  "prompt": "Write a haiku about AI",
  "results": [
    {
      "provider": "openai",
      "content": "Silicon minds think\nBeyond human comprehension\nFuture unfolds now",
      "response_time": 1.2,
      "cost": 0.0001
    },
    {
      "provider": "claude", 
      "content": "Code learns and grows wise\nAlgorithms dance with data\nMachine dreams arise",
      "response_time": 0.8,
      "cost": 0.00008
    }
  ]
}
```

## Analytics & Monitoring

### Usage Statistics

```http
GET /api/llm/analytics/usage
```

**Query Parameters:**
- `period` (string): time, day, week, month (default: day)
- `provider` (string, optional): Filter by provider
- `user_id` (int, optional): Filter by user

**Response:**
```json
{
  "period": "day",
  "total_requests": 1250,
  "total_tokens": 125000,
  "total_cost": 2.50,
  "by_provider": {
    "openai": {
      "requests": 800,
      "tokens": 80000,
      "cost": 1.60
    },
    "claude": {
      "requests": 450,
      "tokens": 45000, 
      "cost": 0.90
    }
  }
}
```

### Provider Health Status

```http
GET /api/llm/analytics/providers/status
```

**Response:**
```json
{
  "providers": [
    {
      "name": "openai",
      "status": "healthy",
      "last_check": "2024-01-15T10:30:00Z",
      "average_response_time": 1.2,
      "success_rate": 99.5
    },
    {
      "name": "claude",
      "status": "healthy", 
      "last_check": "2024-01-15T10:30:00Z",
      "average_response_time": 0.8,
      "success_rate": 99.8
    }
  ]
}
```

### Health Check All Providers

```http
GET /api/llm/analytics/health
```

**Response:**
```json
{
  "overall_status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "providers": {
    "openai": {
      "status": "healthy",
      "response_time": 1.1
    },
    "claude": {
      "status": "healthy",
      "response_time": 0.9
    },
    "groq": {
      "status": "degraded",
      "response_time": 5.2,
      "error": "High latency detected"
    }
  }
}
```

### Cost Estimation

```http
POST /api/llm/analytics/cost/estimate
```

**Request Body:**
```json
{
  "prompt": "Analyze this data...",
  "provider": "openai",
  "model": "gpt-4",
  "max_tokens": 500
}
```

**Response:**
```json
{
  "provider": "openai",
  "model": "gpt-4",
  "estimated_prompt_tokens": 15,
  "estimated_completion_tokens": 500,
  "estimated_total_tokens": 515,
  "estimated_cost": 0.0154
}
```

## Configuration Management

### Get Configuration

```http
GET /api/llm/config
```

**Response (safe config only):**
```json
{
  "enabled_providers": ["openai", "claude", "groq"],
  "default_provider": "openai",
  "rate_limits": {
    "requests_per_minute": 60,
    "requests_per_hour": 1000
  },
  "features": {
    "caching_enabled": true,
    "cost_tracking_enabled": true
  }
}
```

### Enable Provider

```http
POST /api/llm/config/providers/{provider}/enable
```

**Response:**
```json
{
  "provider": "openai",
  "enabled": true,
  "message": "Provider enabled successfully"
}
```

### Disable Provider

```http
POST /api/llm/config/providers/{provider}/disable
```

**Response:**
```json
{
  "provider": "openai", 
  "enabled": false,
  "message": "Provider disabled successfully"
}
```

### Set Default Provider

```http
PUT /api/llm/config/default-provider
```

**Request Body:**
```json
{
  "provider": "claude"
}
```

**Response:**
```json
{
  "default_provider": "claude",
  "message": "Default provider updated successfully"
}
```

## E-commerce Endpoints

### Products

#### List Products

```http
GET /api/products
```

**Query Parameters:**
- `category` (string, optional): Filter by category
- `search` (string, optional): Search in name/description
- `limit` (int, optional): Results per page (default: 20)
- `offset` (int, optional): Number to skip (default: 0)
- `sort` (string, optional): Sort field (name, price, created_at)
- `order` (string, optional): asc or desc (default: asc)

**Response:**
```json
{
  "products": [
    {
      "id": 1,
      "name": "AI Writing Assistant",
      "description": "Advanced AI-powered writing tool",
      "price": 29.99,
      "category": "productivity",
      "rating": 4.5,
      "image_url": "/images/product1.jpg"
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

#### Get Product Details

```http
GET /api/products/{id}
```

**Response:**
```json
{
  "id": 1,
  "name": "AI Writing Assistant",
  "description": "Advanced AI-powered writing tool...",
  "full_description": "Detailed product description...",
  "price": 29.99,
  "category": "productivity",
  "rating": 4.5,
  "reviews_count": 127,
  "features": ["Feature 1", "Feature 2"],
  "requirements": {
    "os": ["Windows", "Mac", "Linux"],
    "ram": "4GB minimum"
  },
  "images": ["/images/product1-1.jpg", "/images/product1-2.jpg"]
}
```

### Orders

#### Create Order

```http
POST /api/orders
```

**Request Body:**
```json
{
  "customer_id": 123,
  "items": [
    {
      "product_id": 1,
      "quantity": 1,
      "price": 29.99
    }
  ],
  "payment_method": "credit_card",
  "billing_address": {
    "line1": "123 Main St",
    "city": "Anytown",
    "state": "CA",
    "postal_code": "12345",
    "country": "US"
  }
}
```

**Response:**
```json
{
  "id": "order-abc-123",
  "status": "pending",
  "total": 29.99,
  "created_at": "2024-01-15T10:30:00Z",
  "items": [...],
  "payment_url": "https://payment-gateway.com/pay/abc123"
}
```

#### Get Order Status

```http
GET /api/orders/{order_id}
```

**Response:**
```json
{
  "id": "order-abc-123",
  "status": "completed",
  "total": 29.99,
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:35:00Z",
  "items": [...],
  "downloads": [
    {
      "product_id": 1,
      "download_url": "https://secure.agentshop.com/download/abc123",
      "license_key": "ABCD-1234-EFGH-5678"
    }
  ]
}
```

### Customers

#### Register Customer

```http
POST /api/customers/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response:**
```json
{
  "id": 123,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "token": "jwt-token-here",
  "message": "Registration successful"
}
```

#### Customer Login

```http
POST /api/customers/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "token": "jwt-token-here",
  "customer": {
    "id": 123,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "expires_at": "2024-01-16T10:30:00Z"
}
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "email",
      "reason": "Invalid email format"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `AUTHENTICATION_REQUIRED` | 401 | Missing or invalid authentication |
| `AUTHORIZATION_FAILED` | 403 | Insufficient permissions |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource doesn't exist |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `PROVIDER_ERROR` | 502 | LLM provider error |
| `INTERNAL_ERROR` | 500 | Server error |

## Rate Limiting

### Default Limits

- **Authenticated users:** 60 requests/minute, 1000 requests/hour
- **LLM endpoints:** 20 requests/minute, 500 requests/hour
- **Anonymous users:** 10 requests/minute, 100 requests/hour

### Rate Limit Headers

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642248600
```

## Pagination

### Standard Pagination

**Query Parameters:**
- `limit`: Number of items per page (max 100)
- `offset`: Number of items to skip

**Response Headers:**
```http
X-Total-Count: 1500
X-Page-Count: 75
Link: </api/products?offset=20&limit=20>; rel="next"
```

## Testing

### Health Check

```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "llm_providers": "healthy",
    "cache": "healthy"
  }
}
```

### Test LLM Provider

```http
POST /api/llm/test
```

**Request Body:**
```json
{
  "provider": "openai",
  "prompt": "Hello, world!"
}
```

**Response:**
```json
{
  "provider": "openai",
  "status": "success",
  "response": "Hello! How can I help you today?",
  "response_time": 1.2
}
```

## SDKs and Client Libraries

### JavaScript/TypeScript

```typescript
import { AgentShopAPI } from '@agentshop/api-client';

const api = new AgentShopAPI('http://localhost:5000');

// Generate text
const response = await api.llm.generate({
  prompt: "Explain AI",
  provider: "openai"
});

// List products
const products = await api.products.list({
  category: "productivity",
  limit: 10
});
```

### Python

```python
from agentshop import AgentShopClient

client = AgentShopClient("http://localhost:5000")

# Generate text
response = client.llm.generate(
    prompt="Explain AI",
    provider="openai"
)

# List products
products = client.products.list(
    category="productivity",
    limit=10
)
```

## Webhooks

### Order Events

```http
POST /webhooks/orders
```

**Payload:**
```json
{
  "event": "order.completed",
  "order_id": "order-abc-123",
  "customer_id": 123,
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "total": 29.99,
    "items": [...]
  }
}
```

### LLM Events

```http
POST /webhooks/llm
```

**Payload:**
```json
{
  "event": "llm.request.completed",
  "request_id": "req-abc-123",
  "provider": "openai",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "tokens_used": 150,
    "cost": 0.003,
    "response_time": 1.2
  }
}
```

---

**For more examples and detailed guides, see the [Developer Documentation](../dev/).**