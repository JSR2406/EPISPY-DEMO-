# Production Deployment Commands - EpiSPY

Complete terminal commands for deploying Resource Marketplace and Personalized Risk systems in production.

## 📋 Prerequisites

### 1. Environment Setup

```bash
# Ensure virtual environment is activated
source epi_stable_env/Scripts/activate  # Windows Git Bash
# OR
source epi_stable_env/bin/activate      # Linux/Mac

# Verify Python version (3.8+)
python --version

# Install all dependencies
pip install -r requirements.txt
```

### 2. Environment Variables

Create/update `.env` file:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/epispy

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
ENCRYPTION_KEY=your-32-char-encryption-key

# Marketplace Settings
MARKETPLACE_AUTO_MATCH_ENABLED=true
MARKETPLACE_AUTO_ACCEPT_THRESHOLD=80.0

# Personalized Risk Settings
RISK_UPDATE_INTERVAL=86400
NOTIFICATION_MAX_DAILY=3
NOTIFICATION_QUIET_HOURS_START=22
NOTIFICATION_QUIET_HOURS_END=7
```

---

## 🗄️ Database Setup

### Step 1: Create Database

```bash
# PostgreSQL
createdb epispy
# OR using psql
psql -U postgres -c "CREATE DATABASE epispy;"
```

### Step 2: Run Migrations

```bash
# Create migration (first time only)
alembic revision --autogenerate -m "Add marketplace and personalized risk models"

# Review the generated migration file in alembic/versions/
# Edit if needed

# Apply migration
alembic upgrade head

# Verify tables created
psql -d epispy -c "\dt" | grep -E "(resource_|user_|volunteer|exposure|risk_history)"
```

### Step 3: Generate Test Data (Optional)

```bash
python scripts/generate_marketplace_test_data.py
```

---

## 🚀 Starting Services

### Option 1: Using Deployment Scripts (Recommended)

```bash
# Make scripts executable (Linux/Mac)
chmod +x scripts/*.sh

# Prepare for deployment
./scripts/deploy_production.sh

# Start all services
./scripts/start_production.sh

# Stop all services
./scripts/stop_production.sh
```

### Option 2: Manual Start (Individual Services)

#### 1. Start API Server

**Development Mode:**
```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Production Mode (Gunicorn):**
```bash
gunicorn src.api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile data/logs/api_access.log \
    --error-logfile data/logs/api_error.log \
    --log-level info
```

**Background (Daemon):**
```bash
gunicorn src.api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile data/logs/api_access.log \
    --error-logfile data/logs/api_error.log \
    --log-level info \
    --daemon \
    --pid /tmp/epispy_api.pid
```

#### 2. Start Celery Workers

**Marketplace Worker:**
```bash
celery -A src.tasks worker \
    --loglevel=info \
    -Q marketplace \
    --concurrency=4 \
    --hostname=marketplace@%h \
    --logfile=data/logs/celery_marketplace.log
```

**Personalized Risk Worker:**
```bash
celery -A src.tasks worker \
    --loglevel=info \
    -Q personalized \
    --concurrency=4 \
    --hostname=personalized@%h \
    --logfile=data/logs/celery_personalized.log
```

**Both Workers (Single Command):**
```bash
celery -A src.tasks worker \
    --loglevel=info \
    -Q marketplace,personalized \
    --concurrency=4 \
    --logfile=data/logs/celery_workers.log
```

**Background (Daemon):**
```bash
# Marketplace worker
celery -A src.tasks worker \
    --loglevel=info \
    -Q marketplace \
    --concurrency=4 \
    --hostname=marketplace@%h \
    --logfile=data/logs/celery_marketplace.log \
    --pidfile=/tmp/celery_marketplace.pid \
    --detach

# Personalized risk worker
celery -A src.tasks worker \
    --loglevel=info \
    -Q personalized \
    --concurrency=4 \
    --hostname=personalized@%h \
    --logfile=data/logs/celery_personalized.log \
    --pidfile=/tmp/celery_personalized.pid \
    --detach
```

#### 3. Start Celery Beat (Scheduler)

```bash
celery -A src.tasks beat \
    --loglevel=info \
    --logfile=data/logs/celery_beat.log
```

**Background (Daemon):**
```bash
celery -A src.tasks beat \
    --loglevel=info \
    --logfile=data/logs/celery_beat.log \
    --pidfile=/tmp/celery_beat.pid \
    --detach
```

#### 4. Start Frontend

**Development:**
```bash
cd frontend
npm install
npm run dev
```

**Production Build:**
```bash
cd frontend
npm install --production
npm run build
npm run preview
```

**Production Serve (Nginx):**
```bash
# Build first
cd frontend
npm run build

# Serve with nginx (configure nginx.conf)
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔍 Health Checks

### Check API Health

```bash
# Basic health check
curl http://localhost:8000/api/v1/health

# Marketplace overview
curl http://localhost:8000/api/v1/marketplace/dashboard/overview

# Database health
curl http://localhost:8000/api/v1/health | jq '.database'
```

### Check Celery Workers

```bash
# List active workers
celery -A src.tasks inspect active

# Check registered tasks
celery -A src.tasks inspect registered

# Check scheduled tasks
celery -A src.tasks inspect scheduled

# Worker stats
celery -A src.tasks inspect stats
```

### Check Redis

```bash
# Test Redis connection
redis-cli ping

# Check Redis info
redis-cli info

# Monitor Redis commands
redis-cli monitor
```

### Check Database

```bash
# Connect to database
psql -d epispy

# Check tables
\dt

# Check table counts
SELECT 
    'resource_providers' as table_name, COUNT(*) as count 
FROM resource_providers
UNION ALL
SELECT 'resource_inventory', COUNT(*) FROM resource_inventory
UNION ALL
SELECT 'resource_requests', COUNT(*) FROM resource_requests
UNION ALL
SELECT 'user_profiles', COUNT(*) FROM user_profiles;
```

---

## 📊 Monitoring Commands

### View Logs

```bash
# API logs
tail -f data/logs/api_access.log
tail -f data/logs/api_error.log

# Celery logs
tail -f data/logs/celery_marketplace.log
tail -f data/logs/celery_personalized.log
tail -f data/logs/celery_beat.log

# All logs
tail -f data/logs/*.log

# Application logs
tail -f data/logs/app.log
```

### Check Process Status

```bash
# Check API process
ps aux | grep gunicorn
ps aux | grep uvicorn

# Check Celery processes
ps aux | grep celery

# Check all EpiSPY processes
ps aux | grep -E "(gunicorn|celery|uvicorn)" | grep -v grep
```

### System Resources

```bash
# CPU and Memory usage
top -p $(pgrep -f "gunicorn|celery")

# Disk usage
df -h

# Database size
psql -d epispy -c "SELECT pg_size_pretty(pg_database_size('epispy'));"
```

---

## 🔧 Maintenance Commands

### Database Backup

```bash
# Backup database
pg_dump -U postgres epispy > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database
psql -U postgres epispy < backup_20240101_120000.sql
```

### Clear Redis Cache

```bash
# Clear all Redis data (use with caution!)
redis-cli FLUSHALL

# Clear specific keys
redis-cli KEYS "epispy:*" | xargs redis-cli DEL
```

### Restart Services

```bash
# Stop all
./scripts/stop_production.sh

# Start all
./scripts/start_production.sh

# Or restart individual service
kill -HUP $(cat /tmp/epispy_api.pid)  # Reload API
```

### Update Code

```bash
# Pull latest code
git pull origin main

# Run migrations if schema changed
alembic upgrade head

# Restart services
./scripts/stop_production.sh
./scripts/start_production.sh
```

---

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### Individual Docker Commands

```bash
# Build API image
docker build -f docker/Dockerfile.api -t epispy-api .

# Run API container
docker run -d \
    --name epispy-api \
    -p 8000:8000 \
    --env-file .env \
    epispy-api

# Run Celery worker
docker run -d \
    --name epispy-celery \
    --env-file .env \
    epispy-api \
    celery -A src.tasks worker -Q marketplace,personalized
```

---

## 🧪 Testing Commands

### Run Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_marketplace.py
pytest tests/test_personalized_risk.py

# With coverage
pytest --cov=src --cov-report=html

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Test API Endpoints

```bash
# Test marketplace endpoint
curl -X POST http://localhost:8000/api/v1/marketplace/providers \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Hospital","provider_type":"HOSPITAL","contact_info":{"email":"test@hospital.com"}}'

# Test risk score endpoint
curl "http://localhost:8000/api/v1/personal/risk-score?user_id=test_user&latitude=19.0760&longitude=72.8777"
```

---

## 📈 Performance Monitoring

### Check API Performance

```bash
# Response time
curl -w "@-" -o /dev/null -s http://localhost:8000/api/v1/health <<'EOF'
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_starttransfer:  %{time_starttransfer}\n
                    ----------\n
         time_total:  %{time_total}\n
EOF

# Load test (install apache bench first)
ab -n 1000 -c 10 http://localhost:8000/api/v1/health
```

### Database Performance

```bash
# Check slow queries
psql -d epispy -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"

# Check table sizes
psql -d epispy -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

---

## 🚨 Troubleshooting

### Service Won't Start

```bash
# Check if port is in use
netstat -tulpn | grep 8000  # Linux
lsof -i :8000               # Mac

# Check logs for errors
tail -n 100 data/logs/api_error.log

# Check environment variables
python -c "from src.utils.config import settings; print(settings.database_url)"
```

### Database Connection Issues

```bash
# Test database connection
psql -d epispy -c "SELECT 1;"

# Check database URL format
echo $DATABASE_URL

# Test async connection
python -c "
import asyncio
from src.database.connection import check_db_health
result = asyncio.run(check_db_health())
print(result)
"
```

### Celery Not Processing Tasks

```bash
# Check worker status
celery -A src.tasks inspect active

# Check if tasks are queued
redis-cli LLEN celery

# Purge all tasks (use with caution!)
celery -A src.tasks purge

# Restart worker
pkill -f "celery.*worker"
celery -A src.tasks worker -Q marketplace,personalized --loglevel=info
```

---

## 📝 Quick Reference

### Most Common Commands

```bash
# Start everything
./scripts/start_production.sh

# Stop everything
./scripts/stop_production.sh

# Check health
curl http://localhost:8000/api/v1/health

# View logs
tail -f data/logs/*.log

# Run migrations
alembic upgrade head

# Restart API
kill -HUP $(cat /tmp/epispy_api.pid)
```

### Service URLs

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/api/v1/health
- **Marketplace**: http://localhost:8000/api/v1/marketplace/dashboard/overview
- **Frontend**: http://localhost:3000 (dev) or http://localhost:80 (prod)

---

## ✅ Production Checklist

Before going live:

- [ ] All environment variables set
- [ ] Database migrations applied
- [ ] Redis running and accessible
- [ ] PostgreSQL running and accessible
- [ ] All services started successfully
- [ ] Health checks passing
- [ ] Logs directory created
- [ ] Firewall rules configured
- [ ] SSL/TLS certificates installed (if using HTTPS)
- [ ] Monitoring set up
- [ ] Backup strategy configured
- [ ] Documentation reviewed

---

**Ready for production!** 🚀

