#!/bin/bash
# Production Deployment Script for EpiSPY Marketplace and Personalized Risk Systems

set -e  # Exit on error

echo "=========================================="
echo "EpiSPY Production Deployment"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "epi_stable_env" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python -m venv epi_stable_env
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source epi_stable_env/Scripts/activate  # Windows
# source epi_stable_env/bin/activate  # Linux/Mac

# Upgrade pip
echo -e "${GREEN}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${GREEN}Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Check database connection
echo -e "${GREEN}Checking database connection...${NC}"
python -c "
from src.utils.config import settings
from src.database.connection import check_db_health
import asyncio
result = asyncio.run(check_db_health())
if result['status'] != 'healthy':
    print('ERROR: Database connection failed!')
    exit(1)
print('Database connection: OK')
"

# Run database migrations
echo -e "${GREEN}Running database migrations...${NC}"
alembic upgrade head

# Verify migrations
echo -e "${GREEN}Verifying database tables...${NC}"
python -c "
from src.database.connection import get_table_info
import asyncio
info = asyncio.run(get_table_info())
tables = [t['name'] for t in info['tables']]
required_tables = [
    'resource_providers', 'resource_inventory', 'resource_requests',
    'resource_matches', 'resource_transfers', 'volunteer_staff',
    'user_profiles', 'user_locations', 'exposure_events', 'risk_history'
]
missing = [t for t in required_tables if t not in tables]
if missing:
    print(f'ERROR: Missing tables: {missing}')
    exit(1)
print('All required tables exist: OK')
"

# Check Redis connection
echo -e "${GREEN}Checking Redis connection...${NC}"
python -c "
from src.cache.redis_client import check_redis_health
import asyncio
result = asyncio.run(check_redis_health())
if result['status'] != 'healthy':
    print('WARNING: Redis connection failed - Celery workers may not work')
else:
    print('Redis connection: OK')
"

echo ""
echo -e "${GREEN}=========================================="
echo "Deployment Complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Start API server: ./scripts/start_api.sh"
echo "2. Start Celery workers: ./scripts/start_workers.sh"
echo "3. Start Celery beat: ./scripts/start_beat.sh"
echo "4. Start frontend: ./scripts/start_frontend.sh"
echo ""
echo "Or use: ./scripts/start_all.sh to start everything"
