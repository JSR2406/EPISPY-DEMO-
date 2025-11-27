# 🚀 Quick Start - Production Deployment

## Windows (Easiest Method)

### 1. Double-click or run:
```cmd
scripts\start_all.bat
```

This opens 4 separate windows automatically:
- API Server (port 8000)
- Marketplace Worker
- Personalized Risk Worker  
- Celery Beat Scheduler

### 2. Verify it's working:
Open browser: **http://localhost:8000/docs**

---

## Manual Setup (Step-by-Step)

### Step 1: Activate Environment
```cmd
epi_stable_env\Scripts\activate.bat
```

### Step 2: Install Dependencies
```cmd
pip install -r requirements.txt
cd frontend
npm install
cd ..
```

### Step 3: Database Migration
```cmd
alembic upgrade head
```

### Step 4: Start Services (5 separate windows)

**Window 1 - API:**
```cmd
epi_stable_env\Scripts\activate.bat
gunicorn src.api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Window 2 - Marketplace Worker:**
```cmd
epi_stable_env\Scripts\activate.bat
celery -A src.tasks worker --loglevel=info -Q marketplace --concurrency=4
```

**Window 3 - Personalized Worker:**
```cmd
epi_stable_env\Scripts\activate.bat
celery -A src.tasks worker --loglevel=info -Q personalized --concurrency=4
```

**Window 4 - Celery Beat:**
```cmd
epi_stable_env\Scripts\activate.bat
celery -A src.tasks beat --loglevel=info
```

**Window 5 - Frontend (Optional):**
```cmd
cd frontend
npm run dev
```

---

## Verify Deployment

1. **API Health:** http://localhost:8000/api/v1/health
2. **API Docs:** http://localhost:8000/docs
3. **Marketplace:** http://localhost:8000/api/v1/marketplace/dashboard/overview

---

## Quick Commands

```cmd
# Check API
curl http://localhost:8000/api/v1/health

# Check workers
celery -A src.tasks inspect active

# Generate test data
python scripts\generate_marketplace_test_data.py
```

---

## Full Documentation

- **Windows Commands:** `PRODUCTION_COMMANDS_WINDOWS.md`
- **Complete Guide:** `PRODUCTION_DEPLOYMENT_COMMANDS.md`
- **Architecture:** `docs/RESOURCE_MARKETPLACE_ARCHITECTURE.md`

---

**That's it! Your production system is running!** 🎉

