# Installation & Setup Guide

Complete guide for installing and setting up AgentShop for development and production.

## Prerequisites

- **Node.js** 16.0+ and npm 8.0+
- **Python** 3.8+
- **Git** for version control

## Quick Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourorg/agentshop.git
cd agentshop
```

### 2. Install Dependencies

```bash
# Install all dependencies (frontend + backend)
npm run install:all
```

This runs:
- `npm install` (root dependencies)
- `cd frontend && npm install` (React dependencies)
- `cd backend && pip install -r requirements.txt` (Python dependencies)

### 3. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Minimum required configuration:**
```env
# Database
DATABASE_URL=sqlite:///agentshop.db

# At least one LLM provider
LLM_OPENAI_ENABLED=true
LLM_OPENAI_API_KEY=sk-your-key-here
```

> **See [Configuration Guide](configuration.md) for all options**

### 4. Initialize Database

```bash
# Database tables are created automatically on first run
npm run backend:dev
```

### 5. Start Development

```bash
# Start both frontend and backend
npm run dev
```

**Access the application:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:5000

## Manual Installation

If you prefer to install components separately:

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Start Services Individually

```bash
# Terminal 1: Backend
npm run backend:dev

# Terminal 2: Frontend  
npm run frontend:dev
```

## Production Installation

See [Deployment Guide](deployment.md) for production setup instructions.

## Troubleshooting

### Common Issues

**SQLAlchemy import errors:**
```bash
pip install --upgrade sqlalchemy
```

**Node module issues:**
```bash
rm -rf node_modules frontend/node_modules
npm run install:all
```

**Permission issues:**
```bash
chmod +x scripts/*.sh
```

### Database Issues

**Reset database:**
```bash
rm agentshop.db
npm run backend:dev  # Recreates tables
```

**View database:**
```bash
sqlite3 agentshop.db
.tables
.schema customers
```

## Development Tools

### Code Quality

```bash
npm run lint              # Lint all code
npm run format            # Format all code
npm run test              # Run all tests
```

### Database Management

```bash
# View database schema
python -c "from backend.models import *; print('Tables created')"

# Create admin user
python scripts/create_admin.py
```

## Next Steps

1. **Configure LLM Providers:** [LLM Provider Setup](llm_providers.md)
2. **Set up Security:** [Security Configuration](security.md)
3. **Deploy to Production:** [Deployment Guide](deployment.md)

## Support

- **Issues:** [GitHub Issues](https://github.com/yourorg/agentshop/issues)
- **Documentation:** [Developer Docs](../dev/)
- **Community:** [Discord/Slack Link]