#!/bin/bash
# Start All Services (Production)

set -e

echo "=========================================="
echo "Starting All EpiSPY Services"
echo "=========================================="
echo ""

# Create logs directory
mkdir -p logs

# Start API server in background
echo "Starting API server..."
./scripts/start_api.sh > logs/api.log 2>&1 &
API_PID=$!
echo "API server started (PID: $API_PID)"
sleep 2

# Start Celery workers
echo "Starting Celery workers..."
./scripts/start_workers.sh > logs/workers.log 2>&1 &
WORKERS_PID=$!
echo "Workers started (PID: $WORKERS_PID)"
sleep 2

# Start Celery beat
echo "Starting Celery beat..."
./scripts/start_beat.sh > logs/beat.log 2>&1 &
BEAT_PID=$!
echo "Beat started (PID: $BEAT_PID)"
sleep 2

# Start frontend (optional, comment out if not needed)
# echo "Starting frontend..."
# ./scripts/start_frontend.sh > logs/frontend.log 2>&1 &
# FRONTEND_PID=$!
# echo "Frontend started (PID: $FRONTEND_PID)"

echo ""
echo "=========================================="
echo "All services started!"
echo "=========================================="
echo ""
echo "Service PIDs:"
echo "  API: $API_PID"
echo "  Workers: $WORKERS_PID"
echo "  Beat: $BEAT_PID"
echo ""
echo "Logs:"
echo "  API: logs/api.log"
echo "  Workers: logs/workers.log"
echo "  Beat: logs/beat.log"
echo ""
echo "To stop all services:"
echo "  kill $API_PID $WORKERS_PID $BEAT_PID"
echo ""
echo "Or use: ./scripts/stop_all.sh"

# Save PIDs to file
echo "$API_PID" > logs/api.pid
echo "$WORKERS_PID" > logs/workers.pid
echo "$BEAT_PID" > logs/beat.pid

# Wait for all processes
wait

