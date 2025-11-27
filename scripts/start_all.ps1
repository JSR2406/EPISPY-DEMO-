# PowerShell script to start all services (Windows)

Write-Host "=========================================="
Write-Host "Starting All EpiSPY Services"
Write-Host "=========================================="
Write-Host ""

# Activate virtual environment
& ".\epi_stable_env\Scripts\Activate.ps1"

# Create logs directory
New-Item -ItemType Directory -Force -Path "logs" | Out-Null

# Start API server
Write-Host "Starting API server..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& '.\epi_stable_env\Scripts\Activate.ps1'; gunicorn src.api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 120" -WindowStyle Normal

Start-Sleep -Seconds 2

# Start Marketplace worker
Write-Host "Starting Marketplace worker..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& '.\epi_stable_env\Scripts\Activate.ps1'; celery -A src.tasks worker --loglevel=info -Q marketplace --concurrency=4 --hostname=marketplace@%h" -WindowStyle Normal

Start-Sleep -Seconds 2

# Start Personalized worker
Write-Host "Starting Personalized Risk worker..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& '.\epi_stable_env\Scripts\Activate.ps1'; celery -A src.tasks worker --loglevel=info -Q personalized --concurrency=4 --hostname=personalized@%h" -WindowStyle Normal

Start-Sleep -Seconds 2

# Start Celery beat
Write-Host "Starting Celery beat..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& '.\epi_stable_env\Scripts\Activate.ps1'; celery -A src.tasks beat --loglevel=info --pidfile=logs/celerybeat.pid" -WindowStyle Normal

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "=========================================="
Write-Host "All services started in separate windows!"
Write-Host "=========================================="
Write-Host ""
Write-Host "API: http://localhost:8000"
Write-Host "Docs: http://localhost:8000/docs"
Write-Host ""
Write-Host "To stop: Close the PowerShell windows or use Ctrl+C"

