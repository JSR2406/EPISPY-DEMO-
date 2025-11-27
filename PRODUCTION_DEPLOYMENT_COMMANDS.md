# Production Deployment Commands - EpiSPY

Complete terminal commands for deploying Resource Marketplace and Personalized Risk systems to production.

## 🚀 Quick Start (All-in-One)

```bash
# 1. Make scripts executable (Linux/Mac)
chmod +x scripts/*.sh

# 2. Deploy everything
./scripts/deploy_production.sh

# 3. Start all services
./scripts/start_all.sh

# 4. Verify deployment
./scripts/verify_deployment.sh
```

---

## 📋 Step-by-Step Production Deployment

### Step 1: Environment Setup

```bash
# Navigate to project directory
cd C:\Users\Janmejay\ Singh\Desktop\EpiSPY

# Activate virtual environment (Windows)
epi_stable_env\Scripts\activate

# Or create if doesn't exist
python -m venv epi_stable_env
epi_stable_env\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip
```

### Step 2: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Step 3: Database Setup

```bash
# Verify database connection
python -c "from src.database.connection import check_db_health; import asyncio; print(asyncio.run(check_db_health()))"

# Create migration (first time only)
alembic revision --autogenerate -m "Add marketplace and personalized risk models"

# Review the migration file in alembic/versions/
# Edit if needed

# Apply migration
alembic upgrade head

# Verify tables created
python -c "
from src.database.connection import get_table_info
import asyncio
info = asyncio.run(get_table_info())
print('Tables:', [t['name'] for t in info['tables']])
"
```

### Step 4: Generate Test Data (Optional)

```bash
# Generate sample data for testing
python scripts/generate_marketplace_test_data.py
```

### Step 5: Start Services

#### Option A: Start All Services (Recommended)

```bash
# Start everything at once
./scripts/start_all.sh

# Or manually start each service in separate terminals
```

#### Option B: Start Services Individually

**Terminal 1 - API Server:**
```bash
# Production mode (Gunicorn)
gunicorn src.api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile logs/api_access.log \
    --error-logfile logs/api_error.log \
    --log-level info

# OR Development mode
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Marketplace Worker:**
```bash
celery -A src.tasks worker \
    --loglevel=info \
    -Q marketplace \
    --concurrency=4 \
    --hostname=marketplace@%h \
    --max-tasks-per-child=1000 \
    --logfile=logs/celery_marketplace.log
```

**Terminal 3 - Personalized Risk Worker:**
```bash
celery -A src.tasks worker \
    --loglevel=info \
    -Q personalized \
    --concurrency=4 \
    --hostname=personalized@%h \
    --max-tasks-per-child=1000 \
    --logfile=logs/celery_personalized.log
```

**Terminal 4 - Celery Beat (Scheduler):**
```bash
celery -A src.tasks beat \
    --loglevel=info \
    --pidfile=logs/celerybeat.pid \
    --logfile=logs/celerybeat.log
```

**Terminal 5 - Frontend (Development):**
```bash
cd frontend
npm run dev
```

**Terminal 6 - Frontend (Production Build):**
```bash
cd frontend
npm run build
npm run preview
# Or serve with nginx/apache
```

### Step 6: Verify Deployment

```bash
# Run verification script
./scripts/verify_deployment.sh

# Or manually verify:

# 1. Check API health
curl http://localhost:8000/api/v1/health

# 2. Check marketplace
curl http://localhost:8000/api/v1/marketplace/dashboard/overview

# 3. Check API docs
# Open browser: http://localhost:8000/docs

# 4. Check Celery workers
celery -A src.tasks inspect active

# 5. Check scheduled tasks
celery -A src.tasks inspect scheduled
```

---

## 🔧 Windows-Specific Commands

### PowerShell Commands

```powershell
# Activate virtual environment
.\epi_stable_env\Scripts\Activate.ps1

# Run deployment
.\scripts\deploy_production.sh

# Start services (use separate PowerShell windows)
# Window 1 - API
gunicorn src.api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Window 2 - Marketplace Worker
celery -A src.tasks worker --loglevel=info -Q marketplace --concurrency=4

# Window 3 - Personalized Worker
celery -A src.tasks worker --loglevel=info -Q personalized --concurrency=4

# Window 4 - Beat
celery -A src.tasks beat --loglevel=info

# Window 5 - Frontend
cd frontend
npm run dev
```

### CMD Commands

```cmd
REM Activate virtual environment
epi_stable_env\Scripts\activate.bat

REM Start API
gunicorn src.api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

REM Start workers (separate CMD windows)
celery -A src.tasks worker --loglevel=info -Q marketplace,personalized

REM Start beat
celery -A src.tasks beat --loglevel=info
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

# Rebuild after changes
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
    --name epispy-worker \
    --env-file .env \
    epispy-api \
    celery -A src.tasks worker -Q marketplace,personalized
```

---

## 🔍 Monitoring Commands

### Check Service Status

```bash
# Check API
curl http://localhost:8000/api/v1/health

# Check Celery workers
celery -A src.tasks inspect active
celery -A src.tasks inspect stats

# Check scheduled tasks
celery -A src.tasks inspect scheduled

# Check registered tasks
celery -A src.tasks inspect registered
```

### View Logs

```bash
# API logs
tail -f logs/api.log
tail -f logs/api_access.log
tail -f logs/api_error.log

# Celery logs
tail -f logs/celery_marketplace.log
tail -f logs/celery_personalized.log
tail -f logs/celerybeat.log

# Application logs
tail -f data/logs/app.log
```

### Database Queries

```bash
# Connect to database
psql -h localhost -U postgres -d epispy

# Check tables
\dt

# Check resource providers
SELECT COUNT(*) FROM resource_providers;

# Check requests
SELECT status, COUNT(*) FROM resource_requests GROUP BY status;

# Check risk scores
SELECT risk_level, COUNT(*) FROM risk_history GROUP BY risk_level;
```

---

## 🛠️ Maintenance Commands

### Database Maintenance

```bash
# Create backup
pg_dump -h localhost -U postgres epispy > backup_$(date +%Y%m%d).sql

# Restore backup
psql -h localhost -U postgres epispy < backup_20240101.sql

# Run migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Show migration history
alembic history
```

### Celery Maintenance

```bash
# Purge all tasks
celery -A src.tasks purge

# Restart workers
pkill -f "celery.*worker"
celery -A src.tasks worker --loglevel=info -Q marketplace,personalized

# Clear scheduled tasks
celery -A src.tasks beat --reset-schedule
```

### Cleanup

```bash
# Clean old logs (keep last 7 days)
find logs -name "*.log" -mtime +7 -delete

# Clean Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# Clean frontend build
cd frontend
rm -rf dist node_modules/.cache
```

---

## 🚨 Troubleshooting

### API Not Starting

```bash
# Check port availability
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Linux/Mac

# Check for errors
python -c "from src.api.main import app; print('API imports OK')"

# Check database connection
python -c "from src.database.connection import check_db_health; import asyncio; print(asyncio.run(check_db_health()))"
```

### Celery Workers Not Running

```bash
# Check Redis connection
redis-cli ping

# Check Celery configuration
celery -A src.tasks inspect ping

# Restart workers
pkill -f "celery.*worker"
celery -A src.tasks worker --loglevel=info -Q marketplace,personalized
```

### Database Issues

```bash
# Check connection
python -c "from src.database.connection import get_database_url; print(get_database_url())"

# Test connection
python -c "
from src.database.connection import create_engine
import asyncio
engine = create_engine()
print('Engine created successfully')
"

# Check migrations
alembic current
alembic history
```

---

## 📊 Production Checklist

Before going live, verify:

- [ ] Database migrations applied
- [ ] Environment variables configured
- [ ] API server running (port 8000)
- [ ] Celery workers running
- [ ] Celery beat running
- [ ] Redis connected
- [ ] Database connected
- [ ] Frontend built and served
- [ ] Health checks passing
- [ ] Logs directory created
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] Error tracking setup (Sentry, etc.)

---

## 🎯 Quick Reference

```bash
# Start everything
./scripts/start_all.sh

# Stop everything
./scripts/stop_all.sh

# Verify deployment
./scripts/verify_deployment.sh

# View logs
tail -f logs/*.log

# Check status
curl http://localhost:8000/api/v1/health
celery -A src.tasks inspect active
```

---

## 📝 Environment Variables

Ensure `.env` file has:

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/epispy
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
SECRET_KEY=your-secret-key
JWT_SECRET=your-jwt-secret
ENCRYPTION_KEY=your-encryption-key
```

---

**All systems ready for production!** 🚀

