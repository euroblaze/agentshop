# AgentShop Project Structure

Complete overview of the AgentShop AI Agent Marketplace project structure and organization.

## 📁 Root Directory Structure

```
agentshop/
├── 📄 new_db.sql                    # Complete database schema
├── 📄 spec.md                       # Project specification
├── 📄 README.md                     # Main project documentation
├── 📄 GROQ_INTEGRATION.md          # Groq LLM integration guide
├── 📄 PROJECT_STRUCTURE.md         # This file
├── 📄 package.json                 # Root package.json for scripts
├── 📄 requirements.txt             # Python dependencies
├── 📄 .env.example                 # Environment configuration template
│
├── 🗂️ backend/                     # Python/Flask backend
├── 🗂️ frontend/                    # TypeScript/React frontend  
├── 🗂️ cli/                         # Command-line tools
├── 🗂️ datalake/                    # Data storage and management
├── 🗂️ automations/                 # Automation scripts and tools
└── 🗂️ docs/                        # Additional documentation
```

## 🔧 Backend Structure

```
backend/
├── 📄 app.py                       # Main Flask application
├── 📄 __init__.py                  # Package initialization
├── 📄 test_groq_integration.py     # Groq integration tests
│
├── 🗂️ orm/                         # Object-Relational Mapping
│   ├── 📄 base_model.py           # Base model and database manager
│   └── 📄 __init__.py
│
├── 🗂️ models/                      # Database models
│   ├── 📄 llm_models.py           # LLM-related models
│   ├── 📄 customer_models.py      # Customer and order models
│   └── 📄 __init__.py
│
├── 🗂️ repositories/                # Data access layer
│   ├── 📄 base_repository.py      # Base repository pattern
│   ├── 📄 llm_repository.py       # LLM data repositories
│   └── 📄 __init__.py
│
├── 🗂️ services/                    # Business logic layer
│   ├── 📄 llm_orm_service.py      # LLM service with ORM integration
│   ├── 🗂️ llm/                    # LLM provider integrations
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base_llm_provider.py
│   │   ├── 📄 ollama_provider.py
│   │   ├── 📄 openai_provider.py
│   │   ├── 📄 claude_provider.py
│   │   ├── 📄 perplexity_provider.py
│   │   ├── 📄 groq_provider.py
│   │   ├── 📄 llm_factory.py
│   │   ├── 📄 llm_service.py
│   │   └── 📄 llm_cache.py
│   └── 📄 __init__.py
│
├── 🗂️ api/                         # REST API endpoints
│   ├── 📄 llm_endpoints.py        # Core LLM operations
│   ├── 📄 llm_chat_endpoints.py   # Chat and conversation APIs
│   ├── 📄 llm_analytics_endpoints.py # Usage analytics APIs
│   ├── 📄 llm_config_endpoints.py # Configuration management APIs
│   └── 📄 __init__.py
│
├── 🗂️ middleware/                  # Request/response middleware
│   ├── 📄 rate_limiter.py         # Rate limiting implementation
│   ├── 📄 error_handler.py        # Error handling and responses
│   └── 📄 __init__.py
│
├── 🗂️ config/                      # Configuration management
│   ├── 📄 llm_config.py           # LLM provider configurations
│   └── 📄 __init__.py
│
└── 🗂️ tests/                       # Backend tests
    ├── 📄 test_llm_providers.py
    ├── 📄 test_api_endpoints.py
    └── 📄 __init__.py
```

## 🎨 Frontend Structure

```
frontend/
├── 📄 package.json                 # Frontend dependencies
├── 📄 tsconfig.json               # TypeScript configuration
├── 📄 vite.config.ts              # Vite build configuration
│
├── 🗂️ src/                         # Source code
│   ├── 📄 main.tsx                # Application entry point
│   ├── 📄 App.tsx                 # Main App component
│   │
│   ├── 🗂️ components/             # React components
│   │   ├── 📄 llm-chat-interface.tsx
│   │   ├── 📄 llm-provider-comparison.tsx
│   │   └── 📄 common/
│   │
│   ├── 🗂️ services/               # API and service layer
│   │   ├── 📄 llm-api-client.ts   # LLM API client
│   │   └── 📄 api-client.ts       # General API client
│   │
│   ├── 🗂️ hooks/                  # Custom React hooks
│   │   ├── 📄 useLLMProvider.ts
│   │   └── 📄 useChat.ts
│   │
│   ├── 🗂️ types/                  # TypeScript type definitions
│   │   ├── 📄 llm.types.ts
│   │   └── 📄 api.types.ts
│   │
│   ├── 🗂️ utils/                  # Utility functions
│   │   └── 📄 formatting.ts
│   │
│   └── 🗂️ styles/                 # CSS and styling
│       ├── 📄 globals.css
│       └── 📄 components.css
│
├── 🗂️ public/                      # Static assets
│   ├── 📄 index.html
│   └── 🗂️ assets/
│
└── 🗂️ dist/                        # Build output
```

## 🛠️ CLI Tools Structure

```
cli/
├── 🗂️ python/                      # Python CLI tools
│   ├── 📄 agentshop_cli.py        # Main Python CLI
│   ├── 📄 requirements.txt        # CLI-specific dependencies
│   └── 📄 README.md               # Python CLI documentation
│
└── 🗂️ typescript/                  # TypeScript CLI tools
    ├── 📄 agentshop-cli.ts        # Main TypeScript CLI
    ├── 📄 package.json            # CLI package configuration
    ├── 📄 tsconfig.json           # TypeScript configuration
    └── 📄 README.md               # TypeScript CLI documentation
```

## 🗄️ Data Lake Structure

```
datalake/
├── 📄 README.md                    # Data lake documentation
│
├── 🗂️ scraped_data/               # External data sources
│   ├── 🗂️ products/              # Competitor product data
│   ├── 🗂️ reviews/               # Customer reviews
│   ├── 🗂️ market_research/       # Industry data
│   ├── 🗂️ content/               # Articles and content
│   └── 📄 .gitkeep
│
├── 🗂️ db_dumps/                   # Database backups
│   ├── 🗂️ daily/                 # Daily automated backups
│   ├── 🗂️ weekly/                # Weekly backups
│   ├── 🗂️ manual/                # Manual backups
│   └── 📄 .gitkeep
│
├── 🗂️ raw_data/                   # Unprocessed data
│   ├── 🗂️ logs/                  # Application logs
│   ├── 🗂️ analytics/             # Raw analytics
│   ├── 🗂️ uploads/               # User uploads
│   ├── 🗂️ imports/               # Data imports
│   └── 📄 .gitkeep
│
├── 🗂️ processed_data/             # Cleaned datasets
│   ├── 🗂️ reports/               # Generated reports
│   ├── 🗂️ exports/               # Data exports
│   ├── 🗂️ ml_datasets/           # ML training data
│   ├── 🗂️ aggregations/          # Statistical summaries
│   └── 📄 .gitkeep
│
└── 🗂️ external_apis/              # Third-party API data
    ├── 🗂️ llm_responses/         # Cached LLM responses
    ├── 🗂️ payment_data/          # Payment information
    ├── 🗂️ shipping_info/         # Logistics data
    └── 🗂️ third_party/           # Other external data
```

## 🤖 Automations Structure

```
automations/
├── 📄 README.md                    # Automation documentation
│
├── 🗂️ webcrawlers/                # Web scraping tools
│   ├── 📄 scoup_client.py         # Scoup microservice integration
│   └── 🗂️ scrapers/              # Custom scrapers
│
├── 🗂️ schedulers/                 # Task scheduling
│   ├── 📄 automation_scheduler.py # Main scheduler
│   ├── 📄 scheduler_config.json   # Task configurations
│   └── 🗂️ jobs/                  # Job definitions
│
├── 🗂️ data_processors/            # Data processing
│   ├── 📄 llm_data_processor.py   # LLM-powered analysis
│   └── 🗂️ processors/            # Custom processors
│
├── 🗂️ notifications/              # Alert systems
│   ├── 📄 email_notifier.py       # Email notifications
│   ├── 📄 slack_notifier.py       # Slack integration
│   ├── 📄 webhook_notifier.py     # Webhook notifications
│   └── 🗂️ templates/             # Notification templates
│
└── 🗂️ logs/                       # Automation logs
    ├── 📄 scheduler.log
    ├── 📄 webcrawler.log
    └── 📄 processor.log
```

## 📊 Database Schema Overview

The `new_db.sql` file contains the complete database schema with the following main table groups:

### Core Tables
- **customers** - User accounts and profiles
- **admin_users** - Administrative users
- **products** - AI agent products for sale
- **orders** - Purchase transactions
- **support_requests** - Customer support

### LLM Integration Tables
- **llm_requests** - All LLM API requests
- **llm_responses** - LLM API responses
- **llm_conversations** - Chat conversation threads
- **llm_conversation_messages** - Individual chat messages
- **llm_usage_stats** - Usage analytics by provider/model
- **llm_provider_status** - Provider health monitoring

### Automation Tables
- **webcrawler_jobs** - Scheduled crawling tasks
- **scraped_data** - Results from web scraping
- **data_processing_tasks** - Data processing jobs

### Configuration Tables
- **config_settings** - System configuration
- **email_templates** - Notification templates

## 🔧 Key Features by Component

### Backend Features
- ✅ **Multi-LLM Support** - Ollama, OpenAI, Claude, Perplexity, Groq
- ✅ **ORM Architecture** - Complete request/response tracking
- ✅ **Conversation Management** - Persistent chat history
- ✅ **Cost Tracking** - Real-time usage and cost monitoring
- ✅ **Rate Limiting** - Configurable limits per endpoint
- ✅ **Caching** - Intelligent response caching
- ✅ **Health Monitoring** - Provider status tracking

### Frontend Features
- ✅ **Chat Interface** - Interactive LLM conversations
- ✅ **Provider Comparison** - Side-by-side testing
- ✅ **Analytics Dashboard** - Usage statistics and costs
- ✅ **Configuration UI** - Provider management
- ✅ **Real-time Updates** - Live conversation sync

### CLI Features
- ✅ **Python CLI** - Full management interface
- ✅ **TypeScript CLI** - Interactive setup and monitoring
- ✅ **Provider Management** - Enable/disable/configure
- ✅ **Data Export** - Usage statistics and reports
- ✅ **Health Checks** - System status monitoring

### Automation Features
- ✅ **Web Crawling** - Scoup microservice integration
- ✅ **Scheduling** - Cron-like task automation
- ✅ **Data Processing** - LLM-powered analysis
- ✅ **Notifications** - Email, Slack, webhook alerts
- ✅ **Data Pipeline** - ETL operations for insights

## 🚀 Getting Started

### 1. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Install all dependencies
npm run install:all
```

### 2. Database Setup
```bash
# Create database with schema
sqlite3 agentshop.db < new_db.sql
```

### 3. Configure LLM Providers
```bash
# Using Python CLI
python cli/python/agentshop_cli.py llm enable openai YOUR_API_KEY

# Using TypeScript CLI
npm run cli:setup
```

### 4. Start Services
```bash
# Start both frontend and backend
npm run dev

# Or individually
npm run backend:dev    # Backend on :5000
npm run frontend:dev   # Frontend on :5173
```

### 5. Start Automations (Optional)
```bash
# Start automation scheduler
cd automations/schedulers
python automation_scheduler.py
```

## 📈 Scaling Considerations

### Horizontal Scaling
- **Load Balancing** - Multiple backend instances
- **Database Sharding** - Partition by customer/provider
- **Caching Layer** - Redis for distributed caching
- **Queue System** - Background job processing

### Performance Optimization
- **Connection Pooling** - Database connection management
- **Response Caching** - LLM response optimization
- **CDN Integration** - Static asset delivery
- **Monitoring** - Application performance tracking

### Security Hardening
- **API Key Rotation** - Automated key management
- **Rate Limiting** - DDoS protection
- **Input Validation** - SQL injection prevention
- **Access Control** - Role-based permissions

## 🔄 Development Workflow

### Code Organization
- **Modular Design** - Clear separation of concerns
- **Type Safety** - Full TypeScript coverage
- **Error Handling** - Comprehensive error management
- **Testing** - Unit and integration tests

### Deployment Pipeline
- **Linting** - Code quality checks
- **Testing** - Automated test suites
- **Building** - Production builds
- **Deployment** - Containerized deployment

This structure provides a scalable, maintainable foundation for the AgentShop AI Agent Marketplace with comprehensive LLM integration, automation capabilities, and data management.