# AgentShop Installation Guide

Complete guide for installing and setting up AgentShop for development and production environments.

## Table of Contents

- [Quick Installation](#quick-installation)
- [Prerequisites](#prerequisites)
- [System Requirements](#system-requirements)
- [Manual Installation](#manual-installation)
- [Database Configuration](#database-configuration)
- [Environment Configuration](#environment-configuration)
- [LLM Integration Setup](#llm-integration-setup)
- [Running the Application](#running-the-application)
- [Development Tools](#development-tools)
- [Production Setup](#production-setup)
- [Troubleshooting](#troubleshooting)

## Quick Installation

For rapid setup (recommended for most users):

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

# Security
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production

# At least one LLM provider (optional)
LLM_OPENAI_ENABLED=true
LLM_OPENAI_API_KEY=sk-your-key-here
```

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
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000

## Prerequisites

### Required Software

- **Python 3.9+** (Backend)
- **Node.js 16+** and **npm/yarn** (Frontend)
- **PostgreSQL 13+** or **MySQL 8+** (Database)
- **Redis 6+** (Caching and sessions)
- **Git** (Version control)

### Optional Tools

- **Docker & Docker Compose** (Containerized development)
- **Postman** or **Insomnia** (API testing)
- **pgAdmin** or **MySQL Workbench** (Database management)

## System Requirements

### Minimum Requirements
- **RAM**: 4GB
- **Storage**: 2GB free space
- **OS**: Windows 10+, macOS 10.15+, or Ubuntu 18.04+

### Recommended Requirements
- **RAM**: 8GB+
- **Storage**: 5GB+ free space
- **CPU**: Multi-core processor

## Manual Installation

If you prefer to install components separately or need more control:

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
# Or using yarn: yarn install
```

### Start Services Individually

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python app.py

# Terminal 2: Frontend  
cd frontend
npm run dev
```

### Directory Structure

After installation, your project structure should look like:

```
agentshop/
├── backend/
│   ├── controllers/     # API endpoint controllers
│   ├── services/        # Business logic services
│   ├── models/          # Database models
│   ├── utils/           # Utilities (serializers, etc.)
│   ├── security/        # Security modules
│   ├── middleware/      # Flask middleware
│   ├── migrations/      # Database migrations
│   ├── app.py          # Flask application entry
│   └── requirements.txt # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── services/    # API client services
│   │   └── models/      # TypeScript models
│   ├── package.json     # Node.js dependencies
│   └── tsconfig.json    # TypeScript configuration
└── .env.example         # Environment template
```

## Database Configuration

### PostgreSQL Setup (Recommended)

#### 1. Install PostgreSQL

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS (using Homebrew)
brew install postgresql
brew services start postgresql

# Windows
# Download from https://www.postgresql.org/download/windows/
```

#### 2. Create Database and User

```bash
# Access PostgreSQL prompt
sudo -u postgres psql

# Create database and user
CREATE DATABASE agentshop_dev;
CREATE USER agentshop_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE agentshop_dev TO agentshop_user;
\q
```

#### 3. Initialize Database Schema

```bash
# Navigate to project root
cd /path/to/agentshop

# Run database initialization script
psql -h localhost -U agentshop_user -d agentshop_dev -f new_db.sql
```

### MySQL Setup (Alternative)

#### 1. Install MySQL

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install mysql-server

# macOS (using Homebrew)
brew install mysql
brew services start mysql

# Windows
# Download from https://dev.mysql.com/downloads/mysql/
```

#### 2. Create Database and User

```sql
mysql -u root -p

CREATE DATABASE agentshop_dev;
CREATE USER 'agentshop_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON agentshop_dev.* TO 'agentshop_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Redis Setup

#### Install Redis

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server

# macOS (using Homebrew)
brew install redis
brew services start redis

# Windows
# Download from https://github.com/microsoftarchive/redis/releases
```

#### Test Redis Connection

```bash
redis-cli ping
# Should return: PONG
```

## Environment Configuration

### 1. Backend Environment Variables

Create `.env` file in the backend directory:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

```env
# Database Configuration
DATABASE_URL=postgresql://agentshop_user:secure_password@localhost/agentshop_dev
# Or for MySQL:
# DATABASE_URL=mysql://agentshop_user:secure_password@localhost/agentshop_dev

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=your-super-secret-key-change-this-in-production

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-change-this-in-production
JWT_ACCESS_TOKEN_EXPIRES=86400  # 24 hours
JWT_REFRESH_TOKEN_EXPIRES=2592000  # 30 days

# Email Configuration (for notifications with Brevo)
MAIL_SERVER=smtp-relay.brevo.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-brevo-login@example.com
MAIL_PASSWORD=your-brevo-smtp-key

# File Upload Configuration
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216  # 16MB

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 2. Frontend Environment Variables

Create `.env` file in the frontend directory:

```bash
cp frontend/.env.example frontend/.env
```

Edit `frontend/.env`:

```env
# API Configuration
REACT_APP_API_BASE_URL=http://localhost:5000/api
REACT_APP_WS_URL=ws://localhost:5000

# App Configuration
REACT_APP_NAME="AgentShop"
REACT_APP_VERSION="1.0.0"

# Feature Flags
REACT_APP_ENABLE_REGISTRATION=true
REACT_APP_ENABLE_PAYMENTS=true
REACT_APP_ENABLE_CHAT=true
```

## LLM Integration Setup

### 1. LLM Provider API Keys

Add LLM provider credentials to `backend/.env`:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key

# Claude (Anthropic) Configuration  
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Groq Configuration
GROQ_API_KEY=gsk_your-groq-api-key

# Ollama Configuration (local)
OLLAMA_BASE_URL=http://localhost:11434

# Perplexity Configuration
PERPLEXITY_API_KEY=pplx-your-perplexity-key
```

### 2. Install Ollama (Optional - Local LLM)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama2

# Start Ollama service
ollama serve
```

## Running the Application

### 1. Start Backend Services

#### Terminal 1: Redis
```bash
redis-server
```

#### Terminal 2: PostgreSQL
```bash
# Usually starts automatically, but you can check:
sudo systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS
```

#### Terminal 3: Flask Backend
```bash
cd backend
source venv/bin/activate  # Activate virtual environment
python app.py

# Or using Flask CLI
export FLASK_APP=app.py
flask run --debug
```

The backend API will be available at: `http://localhost:5000`

### 2. Start Frontend Development Server

#### Terminal 4: React Frontend
```bash
cd frontend
npm start

# Or using yarn
yarn start
```

The frontend will be available at: `http://localhost:3000`

### 3. Verify Installation

#### Check Backend Health
```bash
curl http://localhost:5000/api/health
```

#### Check Frontend
Open your browser and navigate to `http://localhost:3000`

#### Test Database Connection
```bash
cd backend
python -c "
from webshop.models import db
from app import create_app
app = create_app()
with app.app_context():
    print('Database connection successful!' if db.engine.execute('SELECT 1').scalar() == 1 else 'Connection failed')
"
```

## Development Tools

### 1. Python CLI Tools

The project includes Python CLI tools for development:

```bash
# Navigate to CLI directory
cd cli/python

# Install CLI tool
pip install -e .

# Use CLI commands
agentshop-cli --help
agentshop-cli llm list-providers
agentshop-cli db migrate
```

### 2. TypeScript CLI Tools

TypeScript CLI tools for frontend development:

```bash
# Navigate to CLI directory  
cd cli/typescript

# Install dependencies
npm install

# Build CLI tool
npm run build

# Use CLI commands
node dist/index.js --help
```

### 3. Database Migrations

#### Create Migration
```bash
cd backend
flask db init  # First time only
flask db migrate -m "Description of changes"
flask db upgrade
```

#### Reset Database
```bash
# WARNING: This will delete all data
flask db downgrade base
flask db upgrade
```

### 4. Testing

#### Backend Tests
```bash
cd backend
pytest tests/ -v
pytest tests/ --coverage
```

#### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

## Troubleshooting

### Common Issues

#### 1. SQLAlchemy Import Errors

**Error**: `ImportError: cannot import name 'BaseModel'`

**Solution**:
```bash
# Upgrade SQLAlchemy
pip install --upgrade sqlalchemy

# Reinstall requirements
pip install -r backend/requirements.txt
```

#### 2. Node Module Issues

**Error**: `Cannot resolve dependency` or `Module not found`

**Solution**:
```bash
# Clear all caches and reinstall
rm -rf node_modules frontend/node_modules
rm package-lock.json frontend/package-lock.json
npm run install:all
```

#### 3. Permission Issues

**Error**: `Permission denied` when running scripts

**Solution**:
```bash
# Make scripts executable
chmod +x scripts/*.sh
```

#### 4. Database Issues

**Reset database:**
```bash
# For SQLite (development)
rm agentshop.db
npm run backend:dev  # Recreates tables

# For PostgreSQL
dropdb agentshop_dev
createdb agentshop_dev
psql -d agentshop_dev -f new_db.sql
```

**View database:**
```bash
# SQLite
sqlite3 agentshop.db
.tables
.schema customers

# PostgreSQL
psql -d agentshop_dev -c "\dt"
```

#### 5. Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Find and kill process using port 5000
lsof -ti:5000 | xargs kill -9

# Or use different port
export PORT=5001
python app.py
```

#### 6. Python Virtual Environment Issues

**Error**: `ModuleNotFoundError` or `command not found`

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Verify activation
which python  # Should show venv path
```

#### 7. LLM API Connection Issues

**Error**: `Authentication failed` or `API key invalid`

**Solution**:
1. Verify API keys in `.env` file
2. Check API key permissions and quotas
3. Test connection manually:

```bash
# Test OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Test Ollama (if using local LLM)
curl http://localhost:11434/api/version
```

### Performance Optimization

#### Backend Optimization
```bash
# Use production WSGI server
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### Frontend Optimization
```bash
# Production build
npm run build

# Analyze bundle size
npm install -g webpack-bundle-analyzer
npx webpack-bundle-analyzer build/static/js/*.js
```

### Development Workflow

#### 1. Daily Development
```bash
# Pull latest changes
git pull origin main

# Activate environment
source venv/bin/activate

# Update dependencies
pip install -r backend/requirements.txt
cd frontend && npm install

# Start development servers
# Backend: python backend/app.py
# Frontend: cd frontend && npm start
```

#### 2. Before Committing
```bash
# Run tests
pytest backend/tests/
cd frontend && npm test

# Format code
black backend/
cd frontend && npm run format

# Run linting
flake8 backend/
cd frontend && npm run lint
```

## Production Setup

For production deployment, see the [Deployment Guide](deployment.md) for complete instructions.

### Quick Production Setup

```bash
# Set production environment
export FLASK_ENV=production

# Use production database
export DATABASE_URL=postgresql://user:password@localhost/agentshop_prod

# Build frontend for production
cd frontend
npm run build

# Start with production server
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Docker Setup (Alternative)

For a containerized development environment:

### 1. Docker Compose Setup

```bash
# Build and start all services
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 2. Docker Services

The `docker-compose.yml` includes:
- **Backend**: Python/Flask API
- **Frontend**: React development server
- **Database**: PostgreSQL
- **Redis**: Caching layer
- **Nginx**: Reverse proxy (production)

### 3. Docker Commands

```bash
# Rebuild specific service
docker-compose build backend

# Execute commands in container
docker-compose exec backend alembic upgrade head
docker-compose exec frontend npm test

# View container status
docker-compose ps
```

## Getting Help

### Documentation
- [API Documentation](../api/README.md)
- [Frontend Components](../frontend/components.md)
- [Database Schema](../database/schema.md)

### Support Channels
- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Email**: dev-support@agentshop.com

### Contributing
See [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines.

---

**Next Steps**: After installation, check out the [Development Guide](./development.md) for coding standards and best practices.