#!/bin/bash
# Script to create Alembic migration for new models

echo "Creating Alembic migration for marketplace and personalized risk models..."

# Activate virtual environment if it exists
if [ -d "epi_stable_env" ]; then
    source epi_stable_env/Scripts/activate  # Windows
    # source epi_stable_env/bin/activate  # Linux/Mac
fi

# Create migration
alembic revision --autogenerate -m "Add marketplace and personalized risk models"

echo "Migration created! Review the file in alembic/versions/ before applying."
echo "To apply: alembic upgrade head"

