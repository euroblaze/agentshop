# Production Deployment Guide

Complete guide for deploying AgentShop to production environments.

## Prerequisites

- **Linux Server** (Ubuntu 20.04+ recommended)
- **Domain Name** with SSL certificate
- **Database** (PostgreSQL 12+ recommended)
- **Python** 3.8+ and Node.js 16+
- **Reverse Proxy** (Nginx recommended)

## Deployment Options

### Option 1: Traditional Server Deployment

**Best for:** Small to medium deployments, full control needed

### Option 2: Docker Deployment

**Best for:** Containerized environments, easier scaling

### Option 3: Cloud Platform Deployment

**Best for:** Managed infrastructure, auto-scaling

## Traditional Server Deployment

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv nodejs npm nginx postgresql postgresql-contrib redis-server

# Install PM2 for process management
sudo npm install -g pm2
```

### 2. Database Setup

```bash
# Create database user
sudo -u postgres createuser --interactive agentshop

# Create database
sudo -u postgres createdb agentshop -O agentshop

# Set password (replace with secure password)
sudo -u postgres psql -c "ALTER USER agentshop PASSWORD 'your-secure-password';"
```

### 3. Application Setup

```bash
# Create application user
sudo adduser --system --group agentshop

# Create application directory
sudo mkdir -p /opt/agentshop
sudo chown agentshop:agentshop /opt/agentshop

# Switch to application user
sudo -u agentshop -i

# Clone repository
cd /opt/agentshop
git clone https://github.com/yourorg/agentshop.git .

# Install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install Node dependencies
npm install
cd frontend && npm install && npm run build
```

### 4. Environment Configuration

```bash
# Create production environment file
sudo -u agentshop nano /opt/agentshop/.env
```

**Production `.env`:**
```env
# Environment
FLASK_ENV=production
FLASK_DEBUG=false

# Database
DATABASE_URL=postgresql://agentshop:your-secure-password@localhost:5432/agentshop

# Security
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-here
CORS_ORIGINS=https://yourdomain.com

# LLM Providers (configure as needed)
LLM_OPENAI_ENABLED=true
LLM_OPENAI_API_KEY=sk-your-openai-key
LLM_CLAUDE_ENABLED=true
LLM_CLAUDE_API_KEY=sk-ant-your-claude-key

# Performance
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
RATE_LIMIT_PER_MINUTE=100

# Logging
LOG_LEVEL=INFO
LOG_FILE=/opt/agentshop/logs/agentshop.log

# Email (configure SMTP)
SMTP_HOST=smtp.yourdomain.com
SMTP_PORT=587
SMTP_USERNAME=noreply@yourdomain.com
SMTP_PASSWORD=your-smtp-password
```

### 5. Process Management with PM2

```bash
# Create PM2 ecosystem file
sudo -u agentshop nano /opt/agentshop/ecosystem.config.js
```

**ecosystem.config.js:**
```javascript
module.exports = {
  apps: [
    {
      name: 'agentshop-backend',
      script: 'venv/bin/python',
      args: '-m flask run',
      cwd: '/opt/agentshop',
      env: {
        FLASK_APP: 'backend/app.py',
        FLASK_ENV: 'production'
      },
      instances: 'max',
      exec_mode: 'cluster',
      max_memory_restart: '1G',
      error_file: '/opt/agentshop/logs/backend-error.log',
      out_file: '/opt/agentshop/logs/backend-out.log',
      log_file: '/opt/agentshop/logs/backend.log'
    }
  ]
};
```

```bash
# Start application with PM2
sudo -u agentshop pm2 start ecosystem.config.js

# Save PM2 configuration
sudo -u agentshop pm2 save

# Setup PM2 startup script
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u agentshop --hp /home/agentshop
```

### 6. Nginx Configuration

```bash
# Create Nginx site configuration
sudo nano /etc/nginx/sites-available/agentshop
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # Frontend (React)
    location / {
        root /opt/agentshop/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Rate limiting
        limit_req zone=api_limit burst=10 nodelay;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:5000/api/health;
        access_log off;
    }
}

# Rate limiting zone
http {
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/agentshop /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7. SSL Certificate with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

## Docker Deployment

### 1. Dockerfile

**Backend Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ ./backend/
COPY core/ ./core/

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run application
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]
```

**Frontend Dockerfile:**
```dockerfile
FROM node:16-alpine as builder

WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci --only=production

COPY frontend/ .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

### 2. Docker Compose

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  database:
    image: postgres:13
    environment:
      POSTGRES_DB: agentshop
      POSTGRES_USER: agentshop
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agentshop"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:6-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    environment:
      - DATABASE_URL=postgresql://agentshop:${DB_PASSWORD}@database:5432/agentshop
      - REDIS_URL=redis://redis:6379
    depends_on:
      database:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      backend:
        condition: service_healthy
    volumes:
      - ./ssl:/etc/nginx/ssl:ro

volumes:
  postgres_data:
```

### 3. Deploy with Docker

```bash
# Create environment file
echo "DB_PASSWORD=your-secure-password" > .env

# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale backend services
docker-compose up -d --scale backend=3
```

## Cloud Platform Deployment

### AWS Deployment

**Using AWS ECS with Fargate:**

1. **Create ECR repositories:**
```bash
aws ecr create-repository --repository-name agentshop-backend
aws ecr create-repository --repository-name agentshop-frontend
```

2. **Build and push images:**
```bash
# Build images
docker build -f Dockerfile.backend -t agentshop-backend .
docker build -f Dockerfile.frontend -t agentshop-frontend .

# Tag and push
docker tag agentshop-backend:latest $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/agentshop-backend:latest
docker push $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/agentshop-backend:latest
```

3. **Create ECS task definition and service**

### Google Cloud Deployment

**Using Cloud Run:**

```bash
# Build and deploy backend
gcloud builds submit --tag gcr.io/$PROJECT_ID/agentshop-backend

gcloud run deploy agentshop-backend \
    --image gcr.io/$PROJECT_ID/agentshop-backend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated

# Deploy frontend to Cloud Storage + CDN
gsutil rsync -r frontend/dist gs://agentshop-frontend
```

### Digital Ocean Deployment

**Using App Platform:**

```yaml
# app.yaml
name: agentshop
services:
- name: backend
  source_dir: /
  dockerfile_path: Dockerfile.backend
  instance_count: 2
  instance_size_slug: basic-xxs
  envs:
  - key: DATABASE_URL
    value: ${DATABASE_URL}
  health_check:
    http_path: /api/health

- name: frontend
  source_dir: /
  dockerfile_path: Dockerfile.frontend
  instance_count: 1
  instance_size_slug: basic-xxs

databases:
- name: agentshop-db
  engine: PG
  version: "13"
```

```bash
doctl apps create --spec app.yaml
```

## Post-Deployment Configuration

### 1. Database Initialization

```bash
# Run database migrations
python scripts/init_database.py

# Create admin user
python scripts/create_admin.py
```

### 2. Health Checks

```bash
# Check backend health
curl https://yourdomain.com/api/health

# Check LLM providers
curl https://yourdomain.com/api/llm/analytics/health

# Check database
curl https://yourdomain.com/api/health/database
```

### 3. Monitoring Setup

**Install monitoring tools:**
```bash
# Install Prometheus Node Exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.3.1/node_exporter-1.3.1.linux-amd64.tar.gz
tar xf node_exporter-1.3.1.linux-amd64.tar.gz
sudo cp node_exporter-1.3.1.linux-amd64/node_exporter /usr/local/bin/

# Create systemd service
sudo nano /etc/systemd/system/node_exporter.service
```

### 4. Backup Strategy

**Database Backups:**
```bash
# Create backup script
cat > /opt/agentshop/scripts/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/agentshop/backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump agentshop > "$BACKUP_DIR/agentshop_$DATE.sql"
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete
EOF

chmod +x /opt/agentshop/scripts/backup.sh

# Add to crontab
echo "0 2 * * * /opt/agentshop/scripts/backup.sh" | sudo crontab -u agentshop -
```

## Security Hardening

### 1. Firewall Configuration

```bash
# UFW firewall rules
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 2. Application Security

**Rate Limiting:**
```nginx
# In Nginx configuration
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=1r/m;
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

location /api/customers/login {
    limit_req zone=login_limit burst=5 nodelay;
    proxy_pass http://localhost:5000;
}
```

**Security Headers:**
```python
# In Flask application
from flask_talisman import Talisman

Talisman(app, force_https=True)
```

### 3. Database Security

```sql
-- Restrict database permissions
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO agentshop;
GRANT ALL ON ALL TABLES IN SCHEMA public TO agentshop;
```

## Performance Optimization

### 1. Database Optimization

```sql
-- Create performance indexes
CREATE INDEX CONCURRENTLY idx_llm_requests_user_provider ON llm_requests(user_id, provider);
CREATE INDEX CONCURRENTLY idx_products_category_status ON products(category_id, status);
CREATE INDEX CONCURRENTLY idx_orders_customer_status ON orders(customer_id, status);

-- Analyze tables
ANALYZE;
```

### 2. Application Optimization

**Redis Caching:**
```python
# Install Redis client
pip install redis

# Configure caching
REDIS_URL=redis://localhost:6379
LLM_CACHE_ENABLED=true
LLM_CACHE_TTL=3600
```

**CDN Setup:**
```nginx
# Nginx static file caching
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    gzip on;
    gzip_types text/css application/javascript image/svg+xml;
}
```

## Monitoring and Maintenance

### 1. Log Management

```bash
# Configure log rotation
sudo nano /etc/logrotate.d/agentshop
```

```
/opt/agentshop/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    missingok
    sharedscripts
    postrotate
        pm2 reload agentshop-backend
    endscript
}
```

### 2. Health Monitoring

**Setup Uptime Monitoring:**
```bash
# Install Uptime Kuma
docker run -d --restart=always -p 3001:3001 -v uptime-kuma:/app/data --name uptime-kuma louislam/uptime-kuma:1
```

### 3. Automated Updates

```bash
# Create update script
cat > /opt/agentshop/scripts/update.sh << 'EOF'
#!/bin/bash
cd /opt/agentshop
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && npm run build
pm2 reload agentshop-backend
EOF

chmod +x /opt/agentshop/scripts/update.sh
```

## Troubleshooting

### Common Issues

**Application won't start:**
```bash
# Check PM2 status
pm2 status
pm2 logs agentshop-backend

# Check database connection
psql -h localhost -U agentshop -d agentshop -c "SELECT 1;"
```

**High response times:**
```bash
# Check database performance
SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;

# Check PM2 metrics
pm2 monit
```

**SSL certificate issues:**
```bash
# Check certificate validity
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/fullchain.pem -text -noout

# Renew certificate
sudo certbot renew
```

## Scaling Considerations

### Horizontal Scaling

1. **Load Balancer** - Add multiple backend instances
2. **Database Replicas** - Read replicas for analytics
3. **CDN** - Static asset distribution
4. **Microservices** - Split LLM and e-commerce services

### Vertical Scaling

1. **CPU/Memory** - Monitor resource usage
2. **Database** - Tune PostgreSQL settings
3. **Caching** - Add Redis cluster
4. **Storage** - SSD for database

---

**For monitoring and maintenance, see [Monitoring Guide](monitoring.md).**