#!/bin/bash
# Start API Server (Production)

set -e

# Activate virtual environment
source epi_stable_env/Scripts/activate  # Windows
# source epi_stable_env/bin/activate  # Linux/Mac

echo "Starting EpiSPY API Server..."

# Production mode with Gunicorn
gunicorn src.api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --reload  # Remove --reload in true production

# Development mode (alternative)
# uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

