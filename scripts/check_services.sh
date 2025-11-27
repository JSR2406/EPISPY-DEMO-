#!/bin/bash
# Health check script for all EpiSPY services

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "EpiSPY Service Health Check"
echo "=========================================="
echo ""

# Check API
echo -n "API Server: "
if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"
    curl -s http://localhost:8000/api/v1/health | python -m json.tool 2>/dev/null || echo "  Response received"
else
    echo -e "${RED}✗ Not responding${NC}"
fi

# Check Database
echo -n "Database: "
python -c "
import asyncio
from src.database.connection import check_db_health
result = asyncio.run(check_db_health())
if result['status'] == 'healthy':
    print('✓ Healthy')
    exit(0)
else:
    print('✗ Unhealthy')
    exit(1)
" 2>/dev/null && echo -e "${GREEN}✓ Healthy${NC}" || echo -e "${RED}✗ Unhealthy${NC}"

# Check Redis
echo -n "Redis: "
python -c "
import asyncio
from src.cache.redis_client import check_redis_health
result = asyncio.run(check_redis_health())
if result['status'] == 'healthy':
    print('✓ Healthy')
    exit(0)
else:
    print('⚠ Unhealthy (non-critical)')
    exit(0)
" 2>/dev/null && echo -e "${GREEN}✓ Healthy${NC}" || echo -e "${YELLOW}⚠ Unhealthy (non-critical)${NC}"

# Check Celery Workers
echo -n "Celery Workers: "
if command -v celery &> /dev/null; then
    WORKERS=$(celery -A src.tasks inspect active 2>/dev/null | grep -c "worker" || echo "0")
    if [ "$WORKERS" -gt 0 ]; then
        echo -e "${GREEN}✓ $WORKERS worker(s) active${NC}"
    else
        echo -e "${RED}✗ No workers active${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Celery command not found${NC}"
fi

# Check Celery Beat
echo -n "Celery Beat: "
if [ -f /tmp/celery_beat.pid ]; then
    PID=$(cat /tmp/celery_beat.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Running (PID: $PID)${NC}"
    else
        echo -e "${RED}✗ PID file exists but process not running${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Not running${NC}"
fi

# Check Process Counts
echo ""
echo "Process Counts:"
echo "  API: $(ps aux | grep -E 'gunicorn|uvicorn' | grep -v grep | wc -l)"
echo "  Celery: $(ps aux | grep celery | grep -v grep | wc -l)"

echo ""
echo "=========================================="

