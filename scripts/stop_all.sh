#!/bin/bash
# Stop All Services

echo "Stopping all EpiSPY services..."

# Read PIDs from files
if [ -f logs/api.pid ]; then
    API_PID=$(cat logs/api.pid)
    if ps -p $API_PID > /dev/null 2>&1; then
        kill $API_PID
        echo "Stopped API server (PID: $API_PID)"
    fi
fi

if [ -f logs/workers.pid ]; then
    WORKERS_PID=$(cat logs/workers.pid)
    if ps -p $WORKERS_PID > /dev/null 2>&1; then
        kill $WORKERS_PID
        echo "Stopped workers (PID: $WORKERS_PID)"
    fi
fi

if [ -f logs/beat.pid ]; then
    BEAT_PID=$(cat logs/beat.pid)
    if ps -p $BEAT_PID > /dev/null 2>&1; then
        kill $BEAT_PID
        echo "Stopped beat (PID: $BEAT_PID)"
    fi
fi

# Also kill by process name (fallback)
pkill -f "gunicorn src.api.main:app" || true
pkill -f "celery.*worker" || true
pkill -f "celery.*beat" || true

echo "All services stopped."

