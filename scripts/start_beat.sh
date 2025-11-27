#!/bin/bash
# Start Celery Beat Scheduler (Production)

set -e

# Activate virtual environment
source epi_stable_env/Scripts/activate  # Windows
# source epi_stable_env/bin/activate  # Linux/Mac

# Create logs directory if it doesn't exist
mkdir -p logs

echo "Starting Celery Beat Scheduler..."

celery -A src.tasks beat \
    --loglevel=info \
    --pidfile=logs/celerybeat.pid \
    --logfile=logs/celerybeat.log \
    --schedule=logs/celerybeat-schedule.db

