# AgentShop - AI Agent Marketplace

AgentShop is a **simplified, startup-focused** online marketplace for AI agent software with integrated LLM capabilities supporting Ollama, OpenAI, Claude, Perplexity, and Groq APIs.

**Built for simplicity and rapid development** - avoiding the friction of one-size-fits-all solutions like Odoo, WordPress, and Shopify.

## Key Features

- **Multi-LLM Integration** - Unified interface for all major AI providers
- **E-commerce Ready** - Complete product, order, and customer management  
- **Analytics & Tracking** - Real-time usage statistics and cost monitoring
- **Chat Interface** - Built-in conversation management with history
- **Security First** - Rate limiting, validation, and audit trails
- **Performance Optimized** - Intelligent caching and simplified architecture

## Simplified Architecture

Our **consolidated architecture** eliminates complexity while maintaining full functionality:

```
agentshop/
├── core/                   # Single source of truth
│   ├── orm/               # Unified database models
│   ├── repositories/      # Consolidated data access
│   └── api/               # Shared API patterns
├── backend/
│   ├── controllers/       # All API endpoints (unified)
│   ├── models/           # All domain models
│   ├── repositories/     # All data access layers
│   └── services/         # Business logic
│       ├── llm/          # AI/ML services
│       └── webshop/      # E-commerce services
├── frontend/             # React interface
└── docs/                 # Comprehensive documentation
    ├── dev/              # Developer guides
    ├── site_admin/       # Admin configuration
    └── user/             # End-user guides
```

## Quick Start

See our [Installation Guide](docs/site_admin/installation.md) for complete setup instructions.

## Documentation

### For Developers
- [**Installation & Setup**](docs/site_admin/installation.md) - Complete installation guide
- [**Configuration**](docs/site_admin/configuration.md) - Environment and API configuration
- [**Project Structure**](docs/dev/PROJECT_STRUCTURE.md) - Codebase overview and architecture
- [**API Reference**](docs/dev/api-reference.md) - Complete API endpoint documentation
- [**Database Schema**](docs/dev/database-schema.md) - Models and relationships

### For Site Administrators  
- [**Deployment Guide**](docs/site_admin/deployment.md) - Production deployment instructions
- [**LLM Provider Setup**](docs/site_admin/llm-providers.md) - Configure AI providers
- [**Security Configuration**](docs/site_admin/security.md) - Security best practices
- [**Monitoring & Analytics**](docs/site_admin/monitoring.md) - System monitoring setup

### For End Users
- [**Getting Started**](docs/user/getting-started.md) - User guide for the platform
- [**Shopping Guide**](docs/user/shopping.md) - How to browse and purchase AI agents
- [**Account Management**](docs/user/account.md) - Managing your account and orders

## Why AgentShop?

### **Startup-Focused Design**
- **Simple Setup:** Get running in minutes, not hours
- **Low Traffic Optimized:** Perfect for 1000+ visitors/day
- **Minimal Complexity:** ~40% fewer files than traditional e-commerce

### **Consolidated Architecture Benefits**
- **Single Source of Truth:** All base implementations in `/core/`
- **Unified Structure:** No more scattered duplicate code
- **Easy Maintenance:** One place to update, everywhere benefits
- **Developer Friendly:** Clear import paths and organized modules

### **Production Ready**
- **Security First:** Built-in rate limiting and validation
- **Analytics Ready:** Comprehensive tracking and monitoring
- **Performance Optimized:** Intelligent caching and streamlined code
- **E-commerce Complete:** Products, orders, customers, and payments

## Contributing

We welcome contributions! See our [Contributing Guide](docs/dev/contributing.md) for complete instructions on development setup, workflow, and guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Built for the AI agent community**
