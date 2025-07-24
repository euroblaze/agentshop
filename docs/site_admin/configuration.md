# Configuration Guide

Complete configuration options for AgentShop.

## Environment Variables

All configuration is done via environment variables in your `.env` file.

### Database Configuration

```env
# Database URL (SQLite for development, PostgreSQL for production)
DATABASE_URL=sqlite:///agentshop.db
# DATABASE_URL=postgresql://user:password@localhost:5432/agentshop

# Database connection pool settings (PostgreSQL only)
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30

# SQL debugging (set to true for development)
SQL_DEBUG=false
```

## LLM Provider Configuration

### OpenAI Configuration

```env
LLM_OPENAI_ENABLED=true
LLM_OPENAI_API_KEY=sk-your-openai-key
LLM_OPENAI_ORGANIZATION=org-your-org-id  # Optional
LLM_OPENAI_DEFAULT_MODEL=gpt-3.5-turbo
```

**Available Models:**
- `gpt-4` - Most capable, higher cost
- `gpt-3.5-turbo` - Fast and efficient
- `gpt-3.5-turbo-16k` - Longer context

### Claude Configuration

```env
LLM_CLAUDE_ENABLED=true
LLM_CLAUDE_API_KEY=sk-ant-your-claude-key
LLM_CLAUDE_DEFAULT_MODEL=claude-3-haiku-20240307
```

**Available Models:**
- `claude-3-opus-20240229` - Most capable
- `claude-3-sonnet-20240229` - Balanced
- `claude-3-haiku-20240307` - Fastest

### Groq Configuration

```env
LLM_GROQ_ENABLED=true
LLM_GROQ_API_KEY=gsk_your-groq-key
LLM_GROQ_DEFAULT_MODEL=llama3-8b-8192
```

**Available Models:**
- `llama3-70b-8192` - Most capable
- `llama3-8b-8192` - Fastest
- `mixtral-8x7b-32768` - Good balance

### Ollama Configuration

```env
LLM_OLLAMA_ENABLED=true
LLM_OLLAMA_BASE_URL=http://localhost:11434
LLM_OLLAMA_DEFAULT_MODEL=llama2
```

**Setup Ollama:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull models
ollama pull llama2
ollama pull codellama
ollama pull mistral
```

### Perplexity Configuration

```env
LLM_PERPLEXITY_ENABLED=true  
LLM_PERPLEXITY_API_KEY=pplx-your-perplexity-key
LLM_PERPLEXITY_DEFAULT_MODEL=llama-3.1-sonar-small-128k-online
```

**Available Models:**
- `llama-3.1-sonar-large-128k-online` - Most capable
- `llama-3.1-sonar-small-128k-online` - Faster
- `llama-3.1-sonar-large-128k-chat` - Offline chat

## Security Configuration

### Authentication & Sessions

```env
# JWT Secret for authentication
JWT_SECRET_KEY=your-super-secret-jwt-key

# Session expiration (in hours)
SESSION_EXPIRE_HOURS=24
ADMIN_SESSION_EXPIRE_HOURS=8

# Password requirements
MIN_PASSWORD_LENGTH=8
REQUIRE_PASSWORD_COMPLEXITY=true
```

### Rate Limiting

```env
# API rate limits (requests per minute)
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10

# LLM-specific rate limits
LLM_RATE_LIMIT_PER_MINUTE=20
LLM_RATE_LIMIT_PER_HOUR=500
```

### CORS Settings

```env
# Allowed origins for CORS
CORS_ORIGINS=http://localhost:5173,https://yourdomain.com

# In production, set specific domains
# CORS_ORIGINS=https://agentshop.com,https://www.agentshop.com
```

## Application Configuration

### Server Settings

```env
# Flask configuration
FLASK_ENV=development  # production for live
FLASK_DEBUG=true       # false for production
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Frontend settings
FRONTEND_URL=http://localhost:5173
```

### Email Configuration

```env
# SMTP settings for email notifications (using Brevo)
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USERNAME=your-brevo-login@example.com
SMTP_PASSWORD=your-brevo-smtp-key
SMTP_USE_TLS=true

# Email sender details
FROM_EMAIL=noreply@agentshop.com
FROM_NAME=AgentShop
```

### File Storage

```env
# Upload settings
UPLOAD_FOLDER=uploads
MAX_UPLOAD_SIZE=10485760  # 10MB in bytes
ALLOWED_EXTENSIONS=jpg,jpeg,png,pdf,txt,md

# For production, use cloud storage
# AWS_S3_BUCKET=agentshop-uploads
# AWS_ACCESS_KEY_ID=your-access-key
# AWS_SECRET_ACCESS_KEY=your-secret-key
```

## Logging Configuration

```env
# Logging levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Log file location
LOG_FILE=logs/agentshop.log

# Log to console in development
LOG_TO_CONSOLE=true
```

## Analytics & Monitoring

```env
# Enable analytics tracking
ANALYTICS_ENABLED=true

# Google Analytics (optional)
GA_TRACKING_ID=GA-123456789

# Health check settings
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_TOKEN=your-health-check-token
```

## Development vs Production

### Development Settings

```env
FLASK_ENV=development
FLASK_DEBUG=true
SQL_DEBUG=true
LOG_LEVEL=DEBUG
LOG_TO_CONSOLE=true
CORS_ORIGINS=http://localhost:5173
```

### Production Settings

```env
FLASK_ENV=production
FLASK_DEBUG=false
SQL_DEBUG=false
LOG_LEVEL=INFO
LOG_TO_CONSOLE=false
CORS_ORIGINS=https://yourdomain.com
```

## Configuration Validation

Test your configuration:

```bash
# Validate environment
python scripts/validate_config.py

# Test LLM providers
python scripts/test_llm_providers.py

# Check database connection
python scripts/test_database.py
```

## Environment Templates

### Minimal `.env` (Development)

```env
DATABASE_URL=sqlite:///agentshop.db
LLM_OPENAI_ENABLED=true
LLM_OPENAI_API_KEY=sk-your-key
JWT_SECRET_KEY=dev-secret-change-in-production
```

### Complete `.env` (Production)

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/agentshop

# LLM Providers
LLM_OPENAI_ENABLED=true
LLM_OPENAI_API_KEY=sk-your-key
LLM_CLAUDE_ENABLED=true
LLM_CLAUDE_API_KEY=sk-ant-your-key

# Security
JWT_SECRET_KEY=super-secure-production-key
CORS_ORIGINS=https://yourdomain.com

# Performance
DB_POOL_SIZE=20
RATE_LIMIT_PER_MINUTE=100

# Monitoring
LOG_LEVEL=INFO
ANALYTICS_ENABLED=true
```

## Troubleshooting

### Configuration Issues

**Invalid API key:**
- Check key format and permissions
- Verify provider account status

**Database connection:**
- Check DATABASE_URL format
- Verify database server is running

**CORS errors:**
- Add your domain to CORS_ORIGINS
- Check protocol (http vs https)

### Testing Configuration

```bash
# Test API endpoints
curl http://localhost:5000/api/health

# Test LLM integration
curl -X POST http://localhost:5000/api/llm/test \
  -H "Content-Type: application/json" \
  -d '{"provider": "openai", "prompt": "Hello"}'
```

## Next Steps

- [**Security Configuration**](security.md) - Secure your installation
- [**Deployment Guide**](deployment.md) - Deploy to production
- [**Monitoring Setup**](monitoring.md) - Set up monitoring and alerts