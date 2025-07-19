# AgentShop - AI Agent Marketplace

AgentShop is an online marketplace for AI agent software with integrated LLM capabilities supporting Ollama, OpenAI, Claude, Perplexity, and Groq APIs.

## Features

 **Multi-LLM Integration** - Unified interface for Ollama, OpenAI, Claude, Perplexity, and Groq  
 **ORM-Based Architecture** - All LLM calls channeled through backend ORM layer  
 **Request Tracking** - Complete logging and tracking of all LLM requests/responses  
 **Cost Management** - Real-time cost tracking and usage limits  
 **Conversation Management** - Persistent chat conversations with history  
 **Provider Comparison** - Side-by-side comparison of LLM providers  
 **Rate Limiting** - Built-in rate limiting and quota management  
 **Caching** - Intelligent response caching for cost optimization  
 **Analytics** - Usage statistics and provider health monitoring  

## Architecture

### Backend (Python/Flask)
```
backend/
├── orm/                    # ORM layer and database models
├── models/                 # Database models for LLM operations
├── repositories/           # Data access layer with repository pattern
├── services/               # Business logic layer
│   ├── llm/               # Core LLM provider integrations
│   └── llm_orm_service.py # ORM integration service
├── api/                   # REST API endpoints
├── middleware/            # Rate limiting and error handling
└── config/                # Configuration management
```

### Frontend (TypeScript/React)
```
frontend/
├── services/              # API client for backend communication
├── components/            # React components for LLM features
└── package.json          # Frontend dependencies
```

## Quick Start

### 1. Install Dependencies

```bash
# Install all dependencies
npm run install:all
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# At minimum, enable one provider:
LLM_OPENAI_ENABLED=true
LLM_OPENAI_API_KEY=your_api_key_here
```

### 3. Start Development Servers

```bash
# Start both frontend and backend
npm run dev

# Or start individually:
npm run backend:dev    # Backend on :5000
npm run frontend:dev   # Frontend on :5173
```

## API Configuration

### Environment Variables

#### OpenAI Configuration
```env
LLM_OPENAI_ENABLED=true
LLM_OPENAI_API_KEY=sk-...
LLM_OPENAI_ORGANIZATION=org-...
LLM_OPENAI_DEFAULT_MODEL=gpt-3.5-turbo
```

#### Claude Configuration  
```env
LLM_CLAUDE_ENABLED=true
LLM_CLAUDE_API_KEY=sk-ant-...
LLM_CLAUDE_DEFAULT_MODEL=claude-3-haiku-20240307
```

#### Ollama Configuration
```env
LLM_OLLAMA_ENABLED=true
LLM_OLLAMA_BASE_URL=http://localhost:11434
LLM_OLLAMA_DEFAULT_MODEL=llama2
```

#### Perplexity Configuration
```env
LLM_PERPLEXITY_ENABLED=true  
LLM_PERPLEXITY_API_KEY=pplx-...
LLM_PERPLEXITY_DEFAULT_MODEL=llama-3.1-sonar-small-128k-online
```

#### Groq Configuration
```env
LLM_GROQ_ENABLED=true
LLM_GROQ_API_KEY=gsk_...
LLM_GROQ_DEFAULT_MODEL=llama3-8b-8192
```

## API Endpoints

### Core LLM Operations
- `GET /api/llm/providers` - List available providers
- `GET /api/llm/models/{provider}` - Get models for provider
- `POST /api/llm/generate` - Generate text via ORM

### Chat Operations  
- `POST /api/llm/chat/message` - Send chat message
- `GET /api/llm/chat/history/{session_id}` - Get conversation history
- `GET /api/llm/chat/conversations/user/{user_id}` - Get user conversations
- `POST /api/llm/chat/compare` - Compare providers

### Analytics & Monitoring
- `GET /api/llm/analytics/usage` - Usage statistics
- `GET /api/llm/analytics/providers/status` - Provider health status
- `GET /api/llm/analytics/health` - Health check all providers
- `POST /api/llm/analytics/cost/estimate` - Estimate request cost

### Configuration Management
- `GET /api/llm/config` - Get configuration (safe)
- `POST /api/llm/config/providers/{provider}/enable` - Enable provider
- `POST /api/llm/config/providers/{provider}/disable` - Disable provider
- `PUT /api/llm/config/default-provider` - Set default provider

## Database Schema

The system uses SQLAlchemy ORM with the following key models:

- **LLMRequest** - All LLM requests with metadata
- **LLMResponse** - LLM responses with usage stats  
- **LLMConversation** - Chat conversation threads
- **LLMConversationMessage** - Individual messages
- **LLMUsageStats** - Usage statistics by provider/model/time
- **LLMProviderStatus** - Provider health and configuration

## Usage Examples

### Basic Text Generation
```javascript
const apiClient = new LLMApiClient('/api/llm');

const response = await apiClient.generate({
  prompt: "Explain quantum computing",
  provider: "openai", 
  model: "gpt-3.5-turbo",
  user_id: 123,
  session_id: "chat-session-1"
});

console.log(response.content);
```

### Chat Conversation
```javascript
const chatResponse = await apiClient.sendChatMessage(
  "Hello, how can you help me?",
  "chat-session-1",
  {
    provider: "claude",
    user_id: 123
  }
);

console.log(chatResponse.content);
```

### Provider Comparison
```javascript
const comparison = await apiClient.compareProviders(
  "Write a haiku about AI",
  ["openai", "claude", "groq", "ollama"],
  { user_id: 123 }
);

console.log(comparison.results);
```

## Security Features

- **Rate Limiting** - Configurable per-endpoint rate limits
- **API Key Management** - Secure storage and rotation
- **Request Validation** - Input sanitization and validation
- **Error Handling** - Comprehensive error categorization
- **Audit Trail** - Complete request/response logging

## Development

### Running Tests
```bash
npm run test              # Run all tests
npm run test:frontend     # Frontend tests only  
npm run test:backend      # Backend tests only
```

### Code Quality
```bash
npm run lint              # Lint all code
npm run format            # Format all code
```

### Database Operations
```bash
# The database is automatically created on first run
# Tables are created via SQLAlchemy ORM models
```

## Architecture Benefits

1. **Unified Interface** - Single API for all LLM providers
2. **Complete Tracking** - Every request logged with metadata
3. **Cost Control** - Real-time cost tracking and limits
4. **Scalable Design** - Repository pattern and ORM architecture
5. **Provider Agnostic** - Easy to add new LLM providers
6. **Conversation Persistence** - Chat history stored in database
7. **Performance Optimized** - Caching and rate limiting built-in

## Documentation

### Developer Documentation
- [**Project Structure**](docs/dev/PROJECT_STRUCTURE.md) - Complete project structure and component overview
- [**Technical Specification**](docs/dev/spec.md) - Detailed technical specifications and requirements
- [**Groq Integration Guide**](docs/dev/GROQ_INTEGRATION.md) - Comprehensive guide for Groq LLM integration

### Additional Resources
- [**Automation System**](automations/README.md) - Web crawling, scheduling, and data processing
- [**CLI Tools**](cli/README.md) - Command-line interfaces for Python and TypeScript

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
