#!/bin/bash
# Start Celery Workers (Production)

set -e

# Activate virtual environment
source epi_stable_env/Scripts/activate  # Windows
# source epi_stable_env/bin/activate  # Linux/Mac

echo "Starting Celery Workers..."

# Start marketplace worker
celery -A src.tasks worker \
    --loglevel=info \
    -Q marketplace \
    --concurrency=4 \
    --hostname=marketplace@%h \
    --max-tasks-per-child=1000 \
    --time-limit=300 \
    --soft-time-limit=240 \
    --logfile=logs/celery_marketplace.log \
    --pidfile=logs/celery_marketplace.pid &

MARKETPLACE_PID=$!
echo "Marketplace worker started (PID: $MARKETPLACE_PID)"

# Start personalized risk worker
celery -A src.tasks worker \
    --loglevel=info \
    -Q personalized \
    --concurrency=4 \
    --hostname=personalized@%h \
    --max-tasks-per-child=1000 \
    --time-limit=300 \
    --soft-time-limit=240 \
    --logfile=logs/celery_personalized.log \
    --pidfile=logs/celery_personalized.pid &

PERSONALIZED_PID=$!
echo "Personalized risk worker started (PID: $PERSONALIZED_PID)"

echo ""
echo "Workers started. PIDs:"
echo "  Marketplace: $MARKETPLACE_PID"
echo "  Personalized: $PERSONALIZED_PID"
echo ""
echo "To stop: kill $MARKETPLACE_PID $PERSONALIZED_PID"

# Wait for workers
wait

