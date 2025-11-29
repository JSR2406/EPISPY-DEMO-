import sys
import traceback

try:
    from src.api.main import app
    print("Import successful")
except Exception:
    traceback.print_exc()
