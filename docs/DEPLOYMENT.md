# EpiSPY Deployment Guide

This guide covers deploying the EpiSPY epidemic prediction system to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Docker Deployment](#docker-deployment)
4. [Manual Deployment](#manual-deployment)
5. [Production Configuration](#production-configuration)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+ recommended) or Windows Server
- **Python**: 3.11 or higher
- **Docker**: 20.10+ (for containerized deployment)
- **Docker Compose**: 2.0+ (for multi-container deployment)
- **Memory**: Minimum 4GB RAM (8GB+ recommended)
- **Storage**: 20GB+ free space
- **CPU**: 2+ cores recommended

### External Services

- **Ollama**: Local or remote Ollama server for LLM inference
- **Redis**: For caching and background tasks (optional but recommended)
- **Database**: PostgreSQL (production) or SQLite (development)

## Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd EpiSPY
```

### 2. Create Environment File

```bash
cp env.example .env
```

### 3. Configure Environment Variables

Edit `.env` file with production values:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Database (Production - use PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/epidemic_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security Keys (GENERATE NEW ONES!)
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
ENCRYPTION_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Ollama
OLLAMA_HOST=http://ollama-server:11434

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/epispy/app.log
```

### 4. Generate Security Keys

**IMPORTANT**: Generate strong, unique keys for production:

```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(32))"
```

## Docker Deployment

### Quick Start

```bash
# Build and start all services
cd docker
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f epidemic-api
```

### Production Docker Compose

For production, use the provided `docker/docker-compose.yml`:

```bash
cd docker
docker-compose -f docker-compose.yml up -d
```

### Services

The Docker setup includes:

- **epidemic-api**: FastAPI backend (port 8000)
- **epidemic-dashboard**: Streamlit dashboard (port 8501)
- **redis**: Redis cache (port 6379)
- **ollama**: Local LLM server (port 11434)
- **chromadb**: Vector database (port 8500)

### Building Custom Images

```bash
# Build API image
docker build -f docker/Dockerfile.api -t epispy-api:latest .

# Build Dashboard image
docker build -f docker/Dockerfile.dashboard -t epispy-dashboard:latest .
```

## Manual Deployment

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
# For SQLite (development)
python -c "from src.data.storage.database import init_database; init_database()"

# For PostgreSQL (production)
# Create database first:
# createdb epidemic_db
# Then run migrations (if applicable)
```

### 3. Start Services

#### API Server (Production)

```bash
# Using Gunicorn (recommended for production)
gunicorn src.api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

# Or using the run script
python run_api.py
```

#### Dashboard

```bash
streamlit run src/dashboard/Home.py \
    --server.port=8501 \
    --server.address=0.0.0.0
```

### 4. Setup Systemd Service (Linux)

Create `/etc/systemd/system/epispy-api.service`:

```ini
[Unit]
Description=EpiSPY API Service
After=network.target

[Service]
Type=simple
User=epispy
WorkingDirectory=/opt/epispy
Environment="PATH=/opt/epispy/venv/bin"
ExecStart=/opt/epispy/venv/bin/gunicorn src.api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable epispy-api
sudo systemctl start epispy-api
sudo systemctl status epispy-api
```

## Production Configuration

### Security Checklist

- [ ] Change all default passwords and API keys
- [ ] Use HTTPS/TLS for all connections
- [ ] Configure firewall rules
- [ ] Enable authentication on all endpoints
- [ ] Set up rate limiting
- [ ] Configure CORS properly
- [ ] Use environment variables for secrets
- [ ] Enable logging and monitoring
- [ ] Set up backup procedures
- [ ] Configure automatic updates

### Reverse Proxy (Nginx)

Example Nginx configuration (`/etc/nginx/sites-available/epispy`):

```nginx
server {
    listen 80;
    server_name api.epispy.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL/TLS Setup

Use Let's Encrypt with Certbot:

```bash
sudo certbot --nginx -d api.epispy.example.com
```

### Database Backup

```bash
# PostgreSQL
pg_dump -U user epidemic_db > backup_$(date +%Y%m%d).sql

# SQLite
cp data/epidemic_data.db backups/backup_$(date +%Y%m%d).db
```

## Monitoring and Maintenance

### Health Checks

```bash
# API health
curl http://localhost:8000/api/v1/health

# Detailed health
curl http://localhost:8000/api/v1/health/detailed

# Metrics
curl http://localhost:8000/api/v1/health/metrics
```

### Log Monitoring

```bash
# View API logs
tail -f data/logs/app.log

# Docker logs
docker-compose logs -f epidemic-api
```

### Performance Monitoring

- Monitor API response times
- Track database query performance
- Monitor memory and CPU usage
- Set up alerts for errors

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

```bash
# Check database is running
psql -U user -d epidemic_db -c "SELECT 1;"

# Verify DATABASE_URL in .env
echo $DATABASE_URL
```

#### 2. Ollama Connection Failed

```bash
# Test Ollama connection
curl http://localhost:11434/api/tags

# Check OLLAMA_HOST in .env
```

#### 3. Port Already in Use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

#### 4. Import Errors

```bash
# Verify PYTHONPATH
export PYTHONPATH=/path/to/EpiSPY:$PYTHONPATH

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# In .env
DEBUG=true
LOG_LEVEL=DEBUG
```

### Getting Help

- Check logs: `data/logs/app.log`
- Review API documentation: `http://localhost:8000/docs`
- Check health endpoint: `http://localhost:8000/api/v1/health/detailed`

## Scaling

### Horizontal Scaling

- Use load balancer (Nginx, HAProxy)
- Deploy multiple API instances
- Use shared database and Redis
- Configure session affinity if needed

### Vertical Scaling

- Increase worker processes
- Add more memory
- Use faster CPU
- Optimize database queries

## Backup and Recovery

### Automated Backups

Set up cron job for daily backups:

```bash
0 2 * * * /opt/epispy/scripts/backup.sh
```

### Recovery Procedure

1. Stop services
2. Restore database backup
3. Restore data files
4. Verify configuration
5. Start services
6. Run health checks

## Security Updates

- Regularly update dependencies: `pip install -r requirements.txt --upgrade`
- Monitor security advisories
- Apply OS patches regularly
- Review and rotate secrets periodically

