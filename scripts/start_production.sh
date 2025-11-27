#!/bin/bash
# Start all production services for EpiSPY
# This script starts all services in the background

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Activate virtual environment
if [ -d "epi_stable_env" ]; then
    source epi_stable_env/Scripts/activate
fi

# Create logs directory
mkdir -p data/logs

echo -e "${GREEN}Starting EpiSPY Production Services...${NC}"
echo ""

# Start API Server (Gunicorn for production)
echo -e "${GREEN}Starting API server...${NC}"
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

echo "✓ API server started (PID: $(cat /tmp/epispy_api.pid))"
echo "  Logs: data/logs/api_*.log"
echo ""

# Start Celery Worker for Marketplace
echo -e "${GREEN}Starting Celery worker (Marketplace)...${NC}"
celery -A src.tasks worker \
    --loglevel=info \
    -Q marketplace \
    --concurrency=4 \
    --hostname=marketplace@%h \
    --logfile=data/logs/celery_marketplace.log \
    --pidfile=/tmp/celery_marketplace.pid \
    --detach

echo "✓ Marketplace worker started (PID: $(cat /tmp/celery_marketplace.pid))"
echo "  Logs: data/logs/celery_marketplace.log"
echo ""

# Start Celery Worker for Personalized Risk
echo -e "${GREEN}Starting Celery worker (Personalized Risk)...${NC}"
celery -A src.tasks worker \
    --loglevel=info \
    -Q personalized \
    --concurrency=4 \
    --hostname=personalized@%h \
    --logfile=data/logs/celery_personalized.log \
    --pidfile=/tmp/celery_personalized.pid \
    --detach

echo "✓ Personalized risk worker started (PID: $(cat /tmp/celery_personalized.pid))"
echo "  Logs: data/logs/celery_personalized.log"
echo ""

# Start Celery Beat (Scheduler)
echo -e "${GREEN}Starting Celery beat (Scheduler)...${NC}"
celery -A src.tasks beat \
    --loglevel=info \
    --logfile=data/logs/celery_beat.log \
    --pidfile=/tmp/celery_beat.pid \
    --detach

echo "✓ Celery beat started (PID: $(cat /tmp/celery_beat.pid))"
echo "  Logs: data/logs/celery_beat.log"
echo ""

# Wait a moment for services to start
sleep 2

# Check service status
echo -e "${GREEN}Checking service status...${NC}"
echo ""

# Check API
if curl -s http://localhost:8000/api/v1/health > /dev/null; then
    echo "✓ API server is responding"
else
    echo "⚠ API server not responding yet"
fi

# Check Celery workers
if [ -f /tmp/celery_marketplace.pid ] && ps -p $(cat /tmp/celery_marketplace.pid) > /dev/null 2>&1; then
    echo "✓ Marketplace worker is running"
else
    echo "⚠ Marketplace worker not running"
fi

if [ -f /tmp/celery_personalized.pid ] && ps -p $(cat /tmp/celery_personalized.pid) > /dev/null 2>&1; then
    echo "✓ Personalized risk worker is running"
else
    echo "⚠ Personalized risk worker not running"
fi

if [ -f /tmp/celery_beat.pid ] && ps -p $(cat /tmp/celery_beat.pid) > /dev/null 2>&1; then
    echo "✓ Celery beat is running"
else
    echo "⚠ Celery beat not running"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "All services started!"
echo "==========================================${NC}"
echo ""
echo "Service URLs:"
echo "  API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Health: http://localhost:8000/api/v1/health"
echo ""
echo "To stop services, run: ./scripts/stop_production.sh"
echo "To view logs: tail -f data/logs/*.log"

