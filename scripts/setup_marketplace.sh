#!/bin/bash
# Setup script for marketplace and personalized risk systems

echo "Setting up Resource Marketplace and Personalized Risk systems..."

# Activate virtual environment
if [ -d "epi_stable_env" ]; then
    source epi_stable_env/Scripts/activate  # Windows
    # source epi_stable_env/bin/activate  # Linux/Mac
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Create test data (optional)
echo "Creating test data..."
python scripts/generate_marketplace_test_data.py

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Start API: uvicorn src.api.main:app --reload"
echo "2. Start Celery workers: celery -A src.tasks worker --loglevel=info"
echo "3. Start Celery beat: celery -A src.tasks beat --loglevel=info"
echo "4. Start frontend: cd frontend && npm run dev"

