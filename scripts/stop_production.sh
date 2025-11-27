#!/bin/bash
# Stop all production services for EpiSPY

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}Stopping EpiSPY Production Services...${NC}"
echo ""

# Stop API Server
if [ -f /tmp/epispy_api.pid ]; then
    PID=$(cat /tmp/epispy_api.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo -e "${GREEN}✓ API server stopped${NC}"
        rm /tmp/epispy_api.pid
    else
        echo -e "${YELLOW}⚠ API server PID file exists but process not running${NC}"
        rm /tmp/epispy_api.pid
    fi
else
    echo -e "${YELLOW}⚠ API server PID file not found${NC}"
fi

# Stop Celery Workers
for worker in marketplace personalized; do
    PID_FILE="/tmp/celery_${worker}.pid"
    if [ -f $PID_FILE ]; then
        PID=$(cat $PID_FILE)
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID
            echo -e "${GREEN}✓ ${worker} worker stopped${NC}"
            rm $PID_FILE
        else
            echo -e "${YELLOW}⚠ ${worker} worker PID file exists but process not running${NC}"
            rm $PID_FILE
        fi
    fi
done

# Stop Celery Beat
if [ -f /tmp/celery_beat.pid ]; then
    PID=$(cat /tmp/celery_beat.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo -e "${GREEN}✓ Celery beat stopped${NC}"
        rm /tmp/celery_beat.pid
    else
        echo -e "${YELLOW}⚠ Celery beat PID file exists but process not running${NC}"
        rm /tmp/celery_beat.pid
    fi
fi

# Kill any remaining Celery processes
pkill -f "celery.*worker" 2>/dev/null && echo -e "${GREEN}✓ Killed remaining Celery workers${NC}"
pkill -f "celery.*beat" 2>/dev/null && echo -e "${GREEN}✓ Killed remaining Celery beat${NC}"

echo ""
echo -e "${GREEN}All services stopped!${NC}"

