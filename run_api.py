#!/usr/bin/env python3
"""
Production-ready API server runner for EpiSPY.
Supports both development and production modes.
"""
import sys
import os
import uvicorn
import argparse
from pathlib import Path

# This script manually fixes the Python path to correctly import modules from the 'src' folder.

# 1. Get the path to the project root directory (which contains the 'src' folder)
# __file__ is this script's path, os.path.dirname gets the directory.
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Add the root directory to the system path.
# This ensures Python can find the 'src' package correctly.
sys.path.insert(0, ROOT_DIR)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import settings to get configuration
try:
    from src.utils.config import settings
except ImportError:
    print("Warning: Could not import settings, using defaults")
    settings = type('Settings', (), {
        'api_host': os.getenv('API_HOST', '127.0.0.1'),
        'api_port': int(os.getenv('API_PORT', 8000)),
        'debug': os.getenv('DEBUG', 'false').lower() == 'true'
    })()


def main():
    """Main entry point for the API server."""
    parser = argparse.ArgumentParser(description="Run EpiSPY API server")
    parser.add_argument(
        "--host",
        default=settings.api_host,
        help=f"Host to bind to (default: {settings.api_host})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.api_port,
        help=f"Port to bind to (default: {settings.api_port})"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=settings.debug,
        help="Enable auto-reload (development mode)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (use 1 for development, 4+ for production)"
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Log level"
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Run in production mode (uses Gunicorn if available)"
    )
    
    args = parser.parse_args()
    
    # Production mode: use Gunicorn if available
    if args.production:
        try:
            import gunicorn.app.base
            from gunicorn.app.wsgiapp import WSGIApplication
            
            class StandaloneApplication(gunicorn.app.base.BaseApplication):
                def __init__(self, app, options=None):
                    self.options = options or {}
                    self.application = app
                    super().__init__()
                
                def load_config(self):
                    for key, value in self.options.items():
                        self.cfg.set(key.lower(), value)
                
                def load(self):
                    return self.application
            
            # Gunicorn configuration
            options = {
                'bind': f'{args.host}:{args.port}',
                'workers': args.workers,
                'worker_class': 'uvicorn.workers.UvicornWorker',
                'timeout': 120,
                'keepalive': 5,
                'accesslog': '-',
                'errorlog': '-',
                'loglevel': args.log_level,
            }
            
            print(f"Starting EpiSPY API server in PRODUCTION mode")
            print(f"Host: {args.host}, Port: {args.port}, Workers: {args.workers}")
            
            # Import app
            from src.api.main import app
            StandaloneApplication(app, options).run()
            
        except ImportError:
            print("Warning: Gunicorn not available, falling back to Uvicorn")
            print("Install with: pip install gunicorn")
            args.production = False
    
    # Development mode or Gunicorn not available: use Uvicorn
    if not args.production:
        print(f"Starting EpiSPY API server from root: {ROOT_DIR}")
        print(f"Mode: {'Development' if args.reload else 'Production'}")
        print(f"Host: {args.host}, Port: {args.port}")
        
        uvicorn.run(
            "src.api.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level,
            workers=args.workers if not args.reload else 1
        )


if __name__ == "__main__":
    main()
