# Production Deployment Commands - Windows

Complete terminal commands for Windows (PowerShell and CMD) to deploy EpiSPY Marketplace and Personalized Risk systems.

## 🚀 Quick Start (Windows)

### Option 1: Using Batch Script (Easiest)

```cmd
REM Double-click or run:
scripts\start_all.bat
```

### Option 2: Using PowerShell Script

```powershell
# Run in PowerShell:
.\scripts\start_all.ps1
```

### Option 3: Manual Commands (Step-by-Step)

---

## 📋 Step-by-Step Production Deployment

### Step 1: Open PowerShell or CMD

**PowerShell:**
```powershell
# Navigate to project
cd "C:\Users\Janmejay Singh\Desktop\EpiSPY"
```

**CMD:**
```cmd
cd "C:\Users\Janmejay Singh\Desktop\EpiSPY"
```

### Step 2: Activate Virtual Environment

**PowerShell:**
```powershell
.\epi_stable_env\Scripts\Activate.ps1
```

**CMD:**
```cmd
epi_stable_env\Scripts\activate.bat
```

### Step 3: Install/Update Dependencies

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Step 4: Database Setup

```powershell
# Check database connection
python -c "from src.database.connection import check_db_health; import asyncio; print(asyncio.run(check_db_health()))"

# Create migration (first time only)
alembic revision --autogenerate -m "Add marketplace and personalized risk models"

# Apply migration
alembic upgrade head

# Verify tables
python -c "from src.database.connection import get_table_info; import asyncio; info = asyncio.run(get_table_info()); print('Tables:', [t['name'] for t in info['tables']])"
```

### Step 5: Generate Test Data (Optional)

```powershell
python scripts\generate_marketplace_test_data.py
```

---

## 🎯 Starting Services (Windows)

### Method 1: All Services at Once (Recommended)

**Using Batch Script:**
```cmd
scripts\start_all.bat
```

**Using PowerShell Script:**
```powershell
.\scripts\start_all.ps1
```

This will open separate windows for each service.

### Method 2: Manual - Separate Windows

Open **5 separate PowerShell or CMD windows** and run:

#### Window 1: API Server

**PowerShell:**
```powershell
cd "C:\Users\Janmejay Singh\Desktop\EpiSPY"
.\epi_stable_env\Scripts\Activate.ps1
gunicorn src.api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 120
```

**CMD:**
```cmd
cd "C:\Users\Janmejay Singh\Desktop\EpiSPY"
epi_stable_env\Scripts\activate.bat
gunicorn src.api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 120
```

**OR Development Mode:**
```powershell
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Window 2: Marketplace Worker

**PowerShell:**
```powershell
cd "C:\Users\Janmejay Singh\Desktop\EpiSPY"
.\epi_stable_env\Scripts\Activate.ps1
celery -A src.tasks worker --loglevel=info -Q marketplace --concurrency=4 --hostname=marketplace@%h
```

**CMD:**
```cmd
cd "C:\Users\Janmejay Singh\Desktop\EpiSPY"
epi_stable_env\Scripts\activate.bat
celery -A src.tasks worker --loglevel=info -Q marketplace --concurrency=4 --hostname=marketplace@%h
```

#### Window 3: Personalized Risk Worker

**PowerShell:**
```powershell
cd "C:\Users\Janmejay Singh\Desktop\EpiSPY"
.\epi_stable_env\Scripts\Activate.ps1
celery -A src.tasks worker --loglevel=info -Q personalized --concurrency=4 --hostname=personalized@%h
```

**CMD:**
```cmd
cd "C:\Users\Janmejay Singh\Desktop\EpiSPY"
epi_stable_env\Scripts\activate.bat
celery -A src.tasks worker --loglevel=info -Q personalized --concurrency=4 --hostname=personalized@%h
```

#### Window 4: Celery Beat (Scheduler)

**PowerShell:**
```powershell
cd "C:\Users\Janmejay Singh\Desktop\EpiSPY"
.\epi_stable_env\Scripts\Activate.ps1
celery -A src.tasks beat --loglevel=info --pidfile=logs\celerybeat.pid
```

**CMD:**
```cmd
cd "C:\Users\Janmejay Singh\Desktop\EpiSPY"
epi_stable_env\Scripts\activate.bat
celery -A src.tasks beat --loglevel=info --pidfile=logs\celerybeat.pid
```

#### Window 5: Frontend (Development)

**PowerShell:**
```powershell
cd "C:\Users\Janmejay Singh\Desktop\EpiSPY\frontend"
npm run dev
```

**CMD:**
```cmd
cd "C:\Users\Janmejay Singh\Desktop\EpiSPY\frontend"
npm run dev
```

**OR Production Build:**
```powershell
cd "C:\Users\Janmejay Singh\Desktop\EpiSPY\frontend"
npm run build
npm run preview
```

---

## ✅ Verification Commands

### Check API Health

**PowerShell:**
```powershell
# Check API
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" | Select-Object -ExpandProperty Content

# Check Marketplace
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/marketplace/dashboard/overview" | Select-Object -ExpandProperty Content
```

**CMD:**
```cmd
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/marketplace/dashboard/overview
```

**Browser:**
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

### Check Celery Workers

```powershell
.\epi_stable_env\Scripts\Activate.ps1
celery -A src.tasks inspect active
celery -A src.tasks inspect stats
```

### Check Database

```powershell
.\epi_stable_env\Scripts\Activate.ps1
python -c "from src.database.connection import check_db_health; import asyncio; print(asyncio.run(check_db_health()))"
```

---

## 🛑 Stopping Services

### Stop All Services

**Close all PowerShell/CMD windows** that are running the services, or:

**PowerShell:**
```powershell
# Stop API
Get-Process | Where-Object {$_.ProcessName -like "*gunicorn*" -or $_.ProcessName -like "*uvicorn*"} | Stop-Process

# Stop Celery
Get-Process | Where-Object {$_.ProcessName -like "*celery*"} | Stop-Process
```

**CMD:**
```cmd
taskkill /F /IM gunicorn.exe
taskkill /F /IM celery.exe
taskkill /F /IM python.exe
```

---

## 📊 Monitoring Commands

### View Logs

**PowerShell:**
```powershell
# View API logs (if logging to file)
Get-Content logs\api.log -Wait

# View Celery logs
Get-Content logs\celery_marketplace.log -Wait
Get-Content logs\celery_personalized.log -Wait
```

**CMD:**
```cmd
type logs\api.log
type logs\celery_marketplace.log
```

### Check Service Status

```powershell
# Check if API is running
Test-NetConnection -ComputerName localhost -Port 8000

# Check Celery workers
.\epi_stable_env\Scripts\Activate.ps1
celery -A src.tasks inspect ping
```

---

## 🔧 Troubleshooting

### Port Already in Use

```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Virtual Environment Issues

```powershell
# Recreate virtual environment
Remove-Item -Recurse -Force epi_stable_env
python -m venv epi_stable_env
.\epi_stable_env\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Celery Not Starting

```powershell
# Check Redis connection
redis-cli ping

# Check Celery config
.\epi_stable_env\Scripts\Activate.ps1
celery -A src.tasks inspect ping
```

---

## 📝 Complete Production Checklist

Before going live:

- [ ] Virtual environment activated
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Database migrations applied (`alembic upgrade head`)
- [ ] Environment variables configured (`.env` file)
- [ ] API server running (Window 1)
- [ ] Marketplace worker running (Window 2)
- [ ] Personalized worker running (Window 3)
- [ ] Celery beat running (Window 4)
- [ ] Frontend running (Window 5) or built
- [ ] Redis server running
- [ ] PostgreSQL server running
- [ ] Health checks passing
- [ ] API docs accessible (http://localhost:8000/docs)

---

## 🎯 Quick Reference

### Start Everything
```cmd
scripts\start_all.bat
```

### Check API
```powershell
Invoke-WebRequest http://localhost:8000/api/v1/health
```

### View API Docs
Open browser: http://localhost:8000/docs

### Check Workers
```powershell
.\epi_stable_env\Scripts\Activate.ps1
celery -A src.tasks inspect active
```

---

## 📚 Additional Resources

- Full documentation: `PRODUCTION_DEPLOYMENT_COMMANDS.md`
- Architecture: `docs/RESOURCE_MARKETPLACE_ARCHITECTURE.md`
- Implementation: `docs/IMPLEMENTATION_SUMMARY.md`
- Deployment guide: `docs/DEPLOYMENT_MARKETPLACE_AND_RISK.md`

---

**Ready for production deployment on Windows!** 🚀

