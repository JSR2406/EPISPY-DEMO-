@echo off
REM Script to run tests for EpiSPY

call epi_stable_env\Scripts\activate.bat

REM Set environment variables for testing
set TESTING=True
set DATABASE_URL=sqlite:///./test_epispy.db

REM Run tests with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

if %ERRORLEVEL% NEQ 0 (
    echo Some tests failed. Check the output above for details.
) else (
    echo All tests passed successfully!
)

pause
