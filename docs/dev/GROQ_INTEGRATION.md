# Groq Integration Guide

AgentShop now supports Groq for ultra-fast LLM inference using their Language Processing Units (LPUs).

## Features

✅ **Ultra-Fast Inference** - Groq's LPUs provide extremely fast token generation  
✅ **Multiple Models** - Support for Llama, Mixtral, and Gemma models  
✅ **Cost-Effective** - Competitive pricing with transparent cost tracking  
✅ **Full Integration** - Works with all AgentShop features (chat, comparison, analytics)  

## Supported Models

| Model | Context | Best For |
|-------|---------|----------|
| `llama3-8b-8192` | 8K | Fast general tasks |
| `llama3-70b-8192` | 8K | Complex reasoning |
| `llama-3.1-8b-instant` | 128K | Long context, speed |
| `llama-3.1-70b-versatile` | 128K | Long context, quality |
| `mixtral-8x7b-32768` | 32K | Code and technical tasks |
| `gemma-7b-it` | 8K | Instruction following |
| `gemma2-9b-it` | 8K | Improved performance |

## Quick Setup

### 1. Get Groq API Key
```bash
# Sign up at https://console.groq.com/
# Get your API key from the dashboard
```

### 2. Configure Environment
```bash
# Add to your .env file
LLM_GROQ_ENABLED=true
LLM_GROQ_API_KEY=gsk_your_api_key_here
LLM_GROQ_DEFAULT_MODEL=llama3-8b-8192
LLM_GROQ_RATE_LIMIT_RPM=60
LLM_GROQ_COST_LIMIT_DAILY=2.0
```

### 3. Install Dependencies
```bash
pip install groq==0.4.1
```

### 4. Test Integration
```bash
cd backend
python test_groq_integration.py
```

## Usage Examples

### Basic Text Generation
```javascript
const response = await apiClient.generate({
  prompt: "Explain quantum computing briefly",
  provider: "groq",
  model: "llama3-8b-8192",
  temperature: 0.7,
  max_tokens: 200
});

console.log(response.content);
```

### Chat Conversation
```javascript
const chatResponse = await apiClient.sendChatMessage(
  "What makes Groq different?",
  "session-123",
  {
    provider: "groq",
    model: "llama3-70b-8192",
    user_id: 123
  }
);
```

### Speed Comparison
```javascript
// Compare Groq's speed against other providers
const comparison = await apiClient.compareProviders(
  "Write a Python function to sort a list",
  ["groq", "openai", "claude"],
  { 
    model: "llama3-8b-8192",  // For Groq
    user_id: 123 
  }
);

console.log("Speed comparison:", comparison.results);
```

## Performance Benefits

### Speed Benchmarks
- **Groq**: ~300+ tokens/second
- **Traditional GPU**: ~50-100 tokens/second
- **API Services**: ~20-50 tokens/second

### Cost Efficiency
```javascript
// Groq pricing is very competitive
const cost = await apiClient.estimateCost(
  "Long prompt here...",
  "groq",
  { model: "llama3-8b-8192" }
);

console.log(`Groq cost: $${cost.estimated_cost}`);
```

## Best Practices

### Model Selection
```javascript
// For speed-critical applications
const fastModel = "llama3-8b-8192";

// For complex reasoning
const smartModel = "llama3-70b-8192";

// For long context
const longContextModel = "llama-3.1-8b-instant";

// For code generation
const codeModel = "mixtral-8x7b-32768";
```

### Optimizing for Speed
```javascript
// Lower temperature for faster, more deterministic responses
const speedOptimized = {
  provider: "groq",
  model: "llama3-8b-8192",
  temperature: 0.1,
  max_tokens: 100
};

// Use streaming for immediate response feedback
const streamingResponse = {
  provider: "groq",
  stream: true,
  model: "llama3-8b-8192"
};
```

### Cost Management
```javascript
// Monitor usage in real-time
const stats = await apiClient.getUsageStatistics('day', 1, 'groq');
console.log("Groq daily usage:", stats);

// Set daily limits in configuration
LLM_GROQ_COST_LIMIT_DAILY=5.0  // $5 daily limit
```

## Advanced Features

### Custom System Prompts
```javascript
const response = await apiClient.sendChatMessage(
  "Analyze this code",
  "session-123",
  {
    provider: "groq",
    model: "mixtral-8x7b-32768",
    context: {
      system_prompt: "You are an expert code reviewer. Provide concise, actionable feedback."
    }
  }
);
```

### Batch Processing
```javascript
// Process multiple requests efficiently
const batchRequests = [
  "Summarize: AI trends in 2024",
  "Translate: Hello world to Spanish", 
  "Code: Python bubble sort"
];

const results = await Promise.all(
  batchRequests.map(prompt => 
    apiClient.generate({
      prompt,
      provider: "groq",
      model: "llama3-8b-8192",
      max_tokens: 100
    })
  )
);
```

## Monitoring & Analytics

### Usage Tracking
```javascript
// Get Groq-specific analytics
const groqStats = await apiClient.getUsageStatistics('day', 7, 'groq');

// Monitor response times
groqStats.forEach(stat => {
  console.log(`${stat.date}: ${stat.average_response_time_ms}ms avg`);
});
```

### Health Monitoring
```javascript
// Check Groq service health
const health = await apiClient.healthCheck();
console.log("Groq status:", health.groq);

// Get detailed provider status
const status = await apiClient.getProviderStatus();
const groqStatus = status.find(s => s.provider === 'groq');
console.log("Groq health:", groqStatus);
```

## Error Handling

### Common Issues
```javascript
try {
  const response = await apiClient.generate({
    prompt: "Test prompt",
    provider: "groq",
    model: "invalid-model"
  });
} catch (error) {
  if (error.message.includes('model')) {
    console.log("Invalid model, using default");
    // Retry with default model
  }
}
```

### Rate Limiting
```javascript
// Groq has generous rate limits, but handle gracefully
if (response.status === 429) {
  console.log("Rate limited, waiting before retry");
  await new Promise(resolve => setTimeout(resolve, 1000));
  // Retry request
}
```

## Integration Testing

Run the test suite to verify everything works:

```bash
cd backend
python test_groq_integration.py
```

Expected output:
```
🧪 Testing Groq Provider Integration
==================================================
🔧 Initializing Groq provider...
✅ Validating configuration...
📋 Getting available models...
   Available models: 12
   - llama2-70b-4096
   - llama3-8b-8192
   - llama3-70b-8192
   - mixtral-8x7b-32768
   - gemma-7b-it
   ... and 7 more

💰 Testing cost estimation...
   Estimated cost for test request: $0.00000001

🚀 Testing text generation...
   Prompt: 'Write a short greeting in one sentence.'
   ✅ Generation successful!
   Response: Hello! I'm here to help you with any questions or tasks you might have.
   Provider: groq
   Model: llama3-8b-8192
   Tokens used: 16
   Cost: $0.00000001
   Cached: False

🎉 All Groq tests passed successfully!
```

## Troubleshooting

### API Key Issues
```bash
# Verify API key format
echo $LLM_GROQ_API_KEY | grep "gsk_"
```

### Model Availability
```bash
# Check available models via API
curl -H "Authorization: Bearer $LLM_GROQ_API_KEY" \
     https://api.groq.com/openai/v1/models
```

### Performance Issues
- Use smaller models for speed (`llama3-8b-8192`)
- Reduce `max_tokens` for faster responses
- Enable streaming for immediate feedback
- Monitor rate limits and costs

## Groq vs Other Providers

| Feature | Groq | OpenAI | Claude | Ollama |
|---------|------|--------|--------|---------|
| Speed | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Cost | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Models | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Setup | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

**Use Groq when:**
- Speed is critical
- Cost efficiency matters
- Working with supported models
- Building real-time applications

**Use others when:**
- Need cutting-edge models (GPT-4, Claude-3)
- Require specialized capabilities
- Privacy is paramount (Ollama)
- Need maximum model variety

## Support

For Groq-specific issues:
- [Groq Documentation](https://console.groq.com/docs)
- [Groq Discord](https://discord.gg/groq)
- [Rate Limits](https://console.groq.com/docs/rate-limits)

For AgentShop integration issues:
- Check the test script output
- Review logs in `/api/llm/analytics/usage`
- Verify configuration in `/api/llm/config`