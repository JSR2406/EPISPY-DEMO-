#!/bin/bash
# Verify Deployment

set -e

echo "=========================================="
echo "Verifying EpiSPY Deployment"
echo "=========================================="
echo ""

# Activate virtual environment
source epi_stable_env/Scripts/activate  # Windows
# source epi_stable_env/bin/activate  # Linux/Mac

# Check API health
echo "1. Checking API health..."
API_RESPONSE=$(curl -s http://localhost:8000/api/v1/health || echo "FAILED")
if [[ "$API_RESPONSE" == *"status"* ]]; then
    echo "   ✅ API is running"
else
    echo "   ❌ API is not responding"
    exit 1
fi

# Check marketplace overview
echo "2. Checking marketplace endpoint..."
MARKETPLACE_RESPONSE=$(curl -s http://localhost:8000/api/v1/marketplace/dashboard/overview || echo "FAILED")
if [[ "$MARKETPLACE_RESPONSE" == *"total_providers"* ]]; then
    echo "   ✅ Marketplace API is working"
else
    echo "   ❌ Marketplace API is not responding"
    exit 1
fi

# Check database
echo "3. Checking database..."
python -c "
from src.database.connection import check_db_health
import asyncio
result = asyncio.run(check_db_health())
if result['status'] == 'healthy':
    print('   ✅ Database is healthy')
else:
    print('   ❌ Database connection failed')
    exit(1)
"

# Check Redis
echo "4. Checking Redis..."
python -c "
from src.cache.redis_client import check_redis_health
import asyncio
result = asyncio.run(check_redis_health())
if result['status'] == 'healthy':
    print('   ✅ Redis is healthy')
else:
    print('   ⚠️  Redis connection failed (Celery may not work)')
"

# Check Celery workers
echo "5. Checking Celery workers..."
CELERY_STATUS=$(celery -A src.tasks inspect active 2>/dev/null || echo "FAILED")
if [[ "$CELERY_STATUS" != "FAILED" ]]; then
    echo "   ✅ Celery workers are active"
else
    echo "   ⚠️  Celery workers may not be running"
fi

# Check API docs
echo "6. Checking API documentation..."
DOCS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs)
if [ "$DOCS_RESPONSE" == "200" ]; then
    echo "   ✅ API documentation is accessible"
else
    echo "   ⚠️  API documentation may not be accessible"
fi

echo ""
echo "=========================================="
echo "Verification Complete!"
echo "=========================================="
echo ""
echo "API: http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo "Marketplace: http://localhost:8000/api/v1/marketplace/dashboard/overview"
echo ""

