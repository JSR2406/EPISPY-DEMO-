import sys
import os
import uvicorn

# This script manually fixes the Python path to correctly import modules from the 'src' folder.

# 1. Get the path to the project root directory (which contains the 'src' folder)
# __file__ is this script's path, os.path.dirname gets the directory.
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Add the root directory to the system path.
# This ensures Python can find the 'src' package correctly.
sys.path.insert(0, ROOT_DIR)

# 3. Start Uvicorn, telling it to load the app from the 'src' package structure.
# It targets src/api/main.py:app
if __name__ == "__main__":
    print(f"Starting FastAPI server from root: {ROOT_DIR}")
    uvicorn.run(
        "src.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
