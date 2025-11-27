# Deployment Guide - Marketplace & Personalized Risk Systems

## Pre-Deployment Checklist

### 1. Database Preparation
- [ ] PostgreSQL database created
- [ ] Database user with proper permissions
- [ ] Backup existing data (if upgrading)
- [ ] Test database connection

### 2. Environment Variables
- [ ] `DATABASE_URL` configured
- [ ] `REDIS_URL` configured (for Celery)
- [ ] `CELERY_BROKER_URL` configured
- [ ] `CELERY_RESULT_BACKEND` configured
- [ ] All API keys configured (if using external services)

### 3. Dependencies
- [ ] All Python packages installed (`pip install -r requirements.txt`)
- [ ] Node.js packages installed (`cd frontend && npm install`)
- [ ] Redis server running
- [ ] PostgreSQL server running

## Deployment Steps

### Step 1: Database Migration

```bash
# Create migration
alembic revision --autogenerate -m "Add marketplace and personalized risk models"

# Review migration file
# Edit if needed

# Apply migration
alembic upgrade head

# Verify tables created
psql -d epispy -c "\dt" | grep -E "(resource_|user_|volunteer|exposure|risk_history)"
```

### Step 2: Generate Test Data (Optional)

```bash
python scripts/generate_marketplace_test_data.py
```

### Step 3: Start Services

#### API Server
```bash
# Development
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Production
gunicorn src.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

#### Celery Workers
```bash
# Marketplace worker
celery -A src.tasks worker \
  --loglevel=info \
  -Q marketplace \
  --concurrency=4 \
  --hostname=marketplace@%h

# Personalized risk worker
celery -A src.tasks worker \
  --loglevel=info \
  -Q personalized \
  --concurrency=4 \
  --hostname=personalized@%h

# Celery beat (scheduler)
celery -A src.tasks beat \
  --loglevel=info \
  --pidfile=/tmp/celerybeat.pid
```

#### Frontend
```bash
cd frontend
npm run build
npm run preview  # Or serve with nginx
```

### Step 4: Verify Deployment

```bash
# Check API health
curl http://localhost:8000/api/v1/health

# Check marketplace overview
curl http://localhost:8000/api/v1/marketplace/dashboard/overview

# Check API docs
open http://localhost:8000/docs
```

## Docker Deployment

### docker-compose.yml Addition

```yaml
services:
  # ... existing services ...
  
  celery-marketplace:
    build: .
    command: celery -A src.tasks worker -Q marketplace --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - redis
      - postgres
  
  celery-personalized:
    build: .
    command: celery -A src.tasks worker -Q personalized --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - redis
      - postgres
  
  celery-beat:
    build: .
    command: celery -A src.tasks beat --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - redis
      - postgres
```

## Monitoring

### Health Checks

```bash
# API health
GET /api/v1/health

# Marketplace health
GET /api/v1/marketplace/dashboard/overview

# Database health
# Check connection and query performance
```

### Key Metrics

**Marketplace**
- Match success rate
- Average match score
- Time to match
- Active requests vs fulfilled

**Personalized Risk**
- Risk score distribution
- Notification delivery rate
- User engagement
- Calculation performance

## Troubleshooting

### Common Issues

1. **Migration fails**
   - Check database connection
   - Verify user permissions
   - Review migration file for conflicts

2. **Celery tasks not running**
   - Check Redis connection
   - Verify worker is connected to broker
   - Check task queue names

3. **API errors**
   - Check database connection
   - Verify all environment variables
   - Review logs for specific errors

4. **Frontend not loading**
   - Check API connection
   - Verify CORS settings
   - Check browser console for errors

## Production Considerations

1. **Security**
   - Use HTTPS
   - Implement authentication
   - Rate limiting
   - Input validation

2. **Performance**
   - Database indexing
   - Query optimization
   - Caching (Redis)
   - CDN for frontend

3. **Scalability**
   - Horizontal scaling for API
   - Multiple Celery workers
   - Database connection pooling
   - Load balancing

4. **Monitoring**
   - Application logs
   - Error tracking (Sentry)
   - Performance monitoring
   - Database monitoring

## Rollback Plan

If issues occur:

```bash
# Rollback migration
alembic downgrade -1

# Stop services
# Restore database backup
# Restart services
```

## Support

For issues or questions:
- Check documentation in `docs/`
- Review API docs at `/docs`
- Check logs in `data/logs/`

