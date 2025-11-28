@echo off
REM Script to set up the development environment for EpiSPY

echo Setting up EpiSPY development environment...

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH. Please install Python 3.8+ and try again.
    pause
    exit /b 1
)

REM Check if virtual environment exists, if not create one
if not exist "epi_stable_env" (
    echo Creating virtual environment...
    python -m venv epi_stable_env
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

REM Activate the virtual environment
call epi_stable_env\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

echo Installing dependencies...
pip install --upgrade pip
if %ERRORLEVEL% NEQ 0 (
    echo Failed to upgrade pip.
    pause
    exit /b 1
)

REM Install project dependencies
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

echo Development environment setup complete!
pause
