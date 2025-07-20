# LLM Provider Setup Guide

Complete guide for configuring and managing AI provider integrations in AgentShop.

## Overview

AgentShop supports multiple LLM providers to give your users choice and redundancy. Each provider offers different capabilities, pricing, and performance characteristics.

## Supported Providers

### OpenAI
- **Models:** GPT-4, GPT-3.5-turbo, GPT-3.5-turbo-16k
- **Strengths:** High quality, broad capabilities, reliable
- **Best for:** General-purpose applications, complex reasoning
- **Cost:** Moderate to high

### Anthropic Claude
- **Models:** Claude-3 Opus, Sonnet, Haiku
- **Strengths:** Safety-focused, excellent reasoning, long context
- **Best for:** Analysis, research, detailed writing
- **Cost:** Moderate

### Groq
- **Models:** Llama3-70B, Llama3-8B, Mixtral-8x7B
- **Strengths:** Ultra-fast inference, cost-effective
- **Best for:** Real-time applications, high-volume usage
- **Cost:** Low

### Ollama (Self-hosted)
- **Models:** Llama2, Mistral, CodeLlama, many others
- **Strengths:** Complete privacy, no API costs, customizable
- **Best for:** Privacy-sensitive applications, high usage
- **Cost:** Infrastructure only

### Perplexity
- **Models:** Llama-3.1-Sonar variants
- **Strengths:** Real-time web search, up-to-date information
- **Best for:** Research, current events, fact-checking
- **Cost:** Moderate

## Provider Configuration

### OpenAI Setup

1. **Get API Key:**
   - Visit [OpenAI Platform](https://platform.openai.com/)
   - Create account or sign in
   - Go to API Keys section
   - Create new secret key

2. **Configure Environment:**
   ```env
   LLM_OPENAI_ENABLED=true
   LLM_OPENAI_API_KEY=sk-your-openai-key-here
   LLM_OPENAI_ORGANIZATION=org-your-org-id  # Optional
   LLM_OPENAI_DEFAULT_MODEL=gpt-3.5-turbo
   ```

3. **Test Configuration:**
   ```bash
   python scripts/test_openai.py
   ```

### Claude Setup

1. **Get API Key:**
   - Visit [Anthropic Console](https://console.anthropic.com/)
   - Create account and verify
   - Navigate to API Keys
   - Generate new key

2. **Configure Environment:**
   ```env
   LLM_CLAUDE_ENABLED=true
   LLM_CLAUDE_API_KEY=sk-ant-your-claude-key
   LLM_CLAUDE_DEFAULT_MODEL=claude-3-haiku-20240307
   ```

3. **Available Models:**
   - `claude-3-opus-20240229` - Most capable, highest cost
   - `claude-3-sonnet-20240229` - Balanced performance
   - `claude-3-haiku-20240307` - Fastest, lowest cost

### Groq Setup

1. **Get API Key:**
   - Visit [Groq Console](https://console.groq.com/)
   - Sign up for account
   - Create API key

2. **Configure Environment:**
   ```env
   LLM_GROQ_ENABLED=true
   LLM_GROQ_API_KEY=gsk_your-groq-key
   LLM_GROQ_DEFAULT_MODEL=llama3-8b-8192
   ```

3. **Model Selection:**
   - `llama3-70b-8192` - Best quality, slower
   - `llama3-8b-8192` - Fast and efficient
   - `mixtral-8x7b-32768` - Large context window

### Ollama Setup (Self-hosted)

1. **Install Ollama:**
   ```bash
   # On Linux/Mac
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # On Windows
   # Download from https://ollama.ai/download
   ```

2. **Download Models:**
   ```bash
   ollama pull llama2
   ollama pull mistral
   ollama pull codellama
   ollama pull llama2:13b  # Larger model
   ```

3. **Configure Environment:**
   ```env
   LLM_OLLAMA_ENABLED=true
   LLM_OLLAMA_BASE_URL=http://localhost:11434
   LLM_OLLAMA_DEFAULT_MODEL=llama2
   ```

4. **Production Setup:**
   ```bash
   # Run as service
   sudo systemctl enable ollama
   sudo systemctl start ollama
   
   # Check status
   ollama list
   ```

### Perplexity Setup

1. **Get API Key:**
   - Visit [Perplexity AI](https://docs.perplexity.ai/)
   - Sign up for API access
   - Generate API key

2. **Configure Environment:**
   ```env
   LLM_PERPLEXITY_ENABLED=true
   LLM_PERPLEXITY_API_KEY=pplx-your-key
   LLM_PERPLEXITY_DEFAULT_MODEL=llama-3.1-sonar-small-128k-online
   ```

## Provider Management

### Enabling/Disabling Providers

**Via Environment Variables:**
```env
LLM_OPENAI_ENABLED=true   # Enable OpenAI
LLM_CLAUDE_ENABLED=false  # Disable Claude
```

**Via Admin API:**
```bash
# Enable provider
curl -X POST http://localhost:5000/api/llm/config/providers/openai/enable

# Disable provider
curl -X POST http://localhost:5000/api/llm/config/providers/openai/disable
```

**Via Admin Interface:**
- Login to admin panel
- Navigate to LLM Configuration
- Toggle provider status

### Setting Default Provider

```bash
curl -X PUT http://localhost:5000/api/llm/config/default-provider \
  -H "Content-Type: application/json" \
  -d '{"provider": "openai"}'
```

### Provider Priority

Set fallback order when primary provider fails:

```env
LLM_PROVIDER_PRIORITY=openai,claude,groq,ollama
```

## Cost Management

### Rate Limiting

**Per Provider Limits:**
```env
# OpenAI limits
OPENAI_RATE_LIMIT_RPM=60
OPENAI_RATE_LIMIT_RPD=1000

# Claude limits  
CLAUDE_RATE_LIMIT_RPM=30
CLAUDE_RATE_LIMIT_RPD=500
```

**Global Limits:**
```env
LLM_RATE_LIMIT_PER_MINUTE=100
LLM_RATE_LIMIT_PER_HOUR=2000
LLM_RATE_LIMIT_PER_DAY=10000
```

### Cost Tracking

**Enable Cost Monitoring:**
```env
COST_TRACKING_ENABLED=true
COST_ALERT_THRESHOLD=100.00  # USD per day
COST_ALERT_EMAIL=admin@yoursite.com
```

**Cost Analysis:**
```bash
# View cost breakdown
python scripts/cost_analysis.py --period week

# Get provider costs
curl http://localhost:5000/api/llm/analytics/costs
```

### Budget Controls

**Set Provider Budgets:**
```env
OPENAI_MONTHLY_BUDGET=500.00
CLAUDE_MONTHLY_BUDGET=300.00
GROQ_MONTHLY_BUDGET=100.00
```

**Automatic Shutoffs:**
```env
AUTO_DISABLE_ON_BUDGET=true
BUDGET_WARNING_THRESHOLD=0.8  # 80% of budget
```

## Performance Optimization

### Caching Configuration

**Enable Response Caching:**
```env
LLM_CACHE_ENABLED=true
LLM_CACHE_TTL=3600  # 1 hour
LLM_CACHE_SIZE=1000  # Max cached responses
```

**Cache Strategy:**
```env
CACHE_IDENTICAL_PROMPTS=true
CACHE_SIMILAR_PROMPTS=false
CACHE_MIN_PROMPT_LENGTH=50
```

### Load Balancing

**Round Robin:**
```env
LLM_LOAD_BALANCING=round_robin
LLM_ACTIVE_PROVIDERS=openai,claude,groq
```

**Performance-based:**
```env
LLM_LOAD_BALANCING=performance
LLM_PERFORMANCE_WINDOW=3600  # 1 hour
```

**Cost-based:**
```env
LLM_LOAD_BALANCING=cost
LLM_COST_PREFERENCE=lowest
```

## Monitoring & Health Checks

### Health Check Configuration

```env
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_INTERVAL=300  # 5 minutes
HEALTH_CHECK_TIMEOUT=30    # 30 seconds
```

### Provider Status Monitoring

**Check All Providers:**
```bash
curl http://localhost:5000/api/llm/analytics/health
```

**Individual Provider:**
```bash
curl http://localhost:5000/api/llm/analytics/providers/openai/status
```

### Performance Metrics

**Response Time Tracking:**
```env
METRICS_ENABLED=true
METRICS_EXPORT_INTERVAL=60
SLOW_RESPONSE_THRESHOLD=5000  # 5 seconds
```

**Usage Analytics:**
```bash
# Provider usage stats
curl http://localhost:5000/api/llm/analytics/usage

# Model performance
curl http://localhost:5000/api/llm/analytics/models/performance
```

## Security Best Practices

### API Key Security

**Environment Management:**
- Never commit API keys to version control
- Use environment-specific key rotation
- Monitor key usage patterns
- Set up usage alerts

**Key Rotation:**
```bash
# Rotate keys monthly
python scripts/rotate_api_keys.py

# Test new keys before switching
python scripts/test_new_keys.py
```

### Access Control

**Provider Access Restrictions:**
```env
ADMIN_ONLY_PROVIDERS=gpt-4,claude-3-opus
PUBLIC_PROVIDERS=gpt-3.5-turbo,llama3-8b
```

**User Quotas:**
```env
USER_DAILY_QUOTA=100
USER_MONTHLY_QUOTA=1000
PREMIUM_USER_MULTIPLIER=5
```

## Troubleshooting

### Common Issues

**API Key Errors:**
```bash
# Validate keys
python scripts/validate_api_keys.py

# Test connectivity
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

**Rate Limit Exceeded:**
- Check provider dashboards
- Adjust rate limit settings
- Implement request queuing

**Provider Downtime:**
- Enable multiple providers
- Set up automatic failover
- Monitor provider status pages

### Debug Mode

**Enable Debugging:**
```env
LLM_DEBUG=true
LLM_LOG_REQUESTS=true
LLM_LOG_RESPONSES=true
```

**View Debug Logs:**
```bash
tail -f logs/llm_debug.log
```

## Provider-Specific Tips

### OpenAI Optimization
- Use `gpt-3.5-turbo` for most use cases
- Reserve `gpt-4` for complex tasks
- Implement prompt caching
- Monitor token usage

### Claude Best Practices
- Leverage long context capabilities
- Use system prompts effectively
- Handle safety filters gracefully
- Monitor message limits

### Groq Performance
- Excellent for real-time chat
- Batch requests when possible
- Monitor queue times
- Use for high-volume scenarios

### Ollama Management
- Keep models updated
- Monitor GPU memory usage
- Use model quantization for speed
- Implement model warming

## Next Steps

1. **Configure Providers** - Set up your chosen providers
2. **Test Integration** - Verify all providers work correctly
3. **Set Up Monitoring** - Enable health checks and alerts
4. **Optimize Performance** - Configure caching and load balancing
5. **Security Review** - Implement security best practices

## Support Resources

- **Provider Documentation** - Links to official docs
- **Community Forum** - Discuss configurations
- **Technical Support** - Get help with setup
- **Status Pages** - Monitor provider uptime