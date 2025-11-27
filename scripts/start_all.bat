@echo off
REM Batch script to start all services (Windows CMD)

echo ==========================================
echo Starting All EpiSPY Services
echo ==========================================
echo.

REM Activate virtual environment
call epi_stable_env\Scripts\activate.bat

REM Create logs directory
if not exist logs mkdir logs

REM Start API server in new window
echo Starting API server...
start "EpiSPY API" cmd /k "epi_stable_env\Scripts\activate.bat && gunicorn src.api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 120"

timeout /t 2 /nobreak >nul

REM Start Marketplace worker in new window
echo Starting Marketplace worker...
start "EpiSPY Marketplace Worker" cmd /k "epi_stable_env\Scripts\activate.bat && celery -A src.tasks worker --loglevel=info -Q marketplace --concurrency=4 --hostname=marketplace@%%h"

timeout /t 2 /nobreak >nul

REM Start Personalized worker in new window
echo Starting Personalized Risk worker...
start "EpiSPY Personalized Worker" cmd /k "epi_stable_env\Scripts\activate.bat && celery -A src.tasks worker --loglevel=info -Q personalized --concurrency=4 --hostname=personalized@%%h"

timeout /t 2 /nobreak >nul

REM Start Celery beat in new window
echo Starting Celery beat...
start "EpiSPY Celery Beat" cmd /k "epi_stable_env\Scripts\activate.bat && celery -A src.tasks beat --loglevel=info --pidfile=logs/celerybeat.pid"

timeout /t 2 /nobreak >nul

echo.
echo ==========================================
echo All services started in separate windows!
echo ==========================================
echo.
echo API: http://localhost:8000
echo Docs: http://localhost:8000/docs
echo.
echo To stop: Close the command windows or use Ctrl+C
echo.
pause

