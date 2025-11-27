#!/usr/bin/env python3
"""
Deployment script for EpiSPY.
Automates common deployment tasks.
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional

# Colors for output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_step(message: str):
    """Print a deployment step message."""
    print(f"{Colors.BLUE}>>> {message}{Colors.END}")


def print_success(message: str):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message: str):
    """Print an error message."""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")


def run_command(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command."""
    print_step(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e}")
        if e.stderr:
            print(e.stderr)
        if check:
            sys.exit(1)
        return e


def check_prerequisites():
    """Check if prerequisites are installed."""
    print_step("Checking prerequisites...")
    
    prerequisites = {
        "python": ["python", "--version"],
        "pip": ["pip", "--version"],
        "docker": ["docker", "--version"],
        "docker-compose": ["docker-compose", "--version"]
    }
    
    missing = []
    for name, cmd in prerequisites.items():
        try:
            run_command(cmd, check=False)
            print_success(f"{name} is installed")
        except FileNotFoundError:
            print_warning(f"{name} is not installed")
            missing.append(name)
    
    if missing:
        print_error(f"Missing prerequisites: {', '.join(missing)}")
        return False
    
    return True


def setup_environment():
    """Set up environment file."""
    print_step("Setting up environment...")
    
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print_step("Creating .env from env.example...")
            env_file.write_text(env_example.read_text())
            print_success(".env file created")
            print_warning("Please edit .env file with your configuration")
        else:
            print_error("env.example not found")
            return False
    else:
        print_success(".env file already exists")
    
    return True


def install_dependencies():
    """Install Python dependencies."""
    print_step("Installing dependencies...")
    
    if not Path("requirements.txt").exists():
        print_error("requirements.txt not found")
        return False
    
    run_command(["pip", "install", "-r", "requirements.txt"])
    print_success("Dependencies installed")
    return True


def initialize_database():
    """Initialize database."""
    print_step("Initializing database...")
    
    try:
        # Add project root to path
        sys.path.insert(0, str(Path.cwd()))
        
        from src.data.storage.database import init_database
        init_database()
        print_success("Database initialized")
        return True
    except Exception as e:
        print_error(f"Database initialization failed: {str(e)}")
        return False


def build_docker_images():
    """Build Docker images."""
    print_step("Building Docker images...")
    
    docker_dir = Path("docker")
    if not docker_dir.exists():
        print_warning("Docker directory not found, skipping Docker build")
        return False
    
    # Build API image
    print_step("Building API image...")
    run_command([
        "docker", "build",
        "-f", "docker/Dockerfile.api",
        "-t", "epispy-api:latest",
        "."
    ])
    
    # Build Dashboard image
    print_step("Building Dashboard image...")
    run_command([
        "docker", "build",
        "-f", "docker/Dockerfile.dashboard",
        "-t", "epispy-dashboard:latest",
        "."
    ])
    
    print_success("Docker images built")
    return True


def start_docker_services():
    """Start Docker services."""
    print_step("Starting Docker services...")
    
    docker_compose = Path("docker/docker-compose.yml")
    if not docker_compose.exists():
        print_warning("docker-compose.yml not found")
        return False
    
    os.chdir("docker")
    run_command(["docker-compose", "up", "-d"])
    os.chdir("..")
    
    print_success("Docker services started")
    return True


def run_tests():
    """Run tests."""
    print_step("Running tests...")
    
    try:
        run_command(["pytest", "src/tests/", "-v"])
        print_success("Tests passed")
        return True
    except FileNotFoundError:
        print_warning("pytest not found, skipping tests")
        return False
    except subprocess.CalledProcessError:
        print_error("Tests failed")
        return False


def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description="Deploy EpiSPY")
    parser.add_argument(
        "--mode",
        choices=["docker", "local", "full"],
        default="full",
        help="Deployment mode"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running tests"
    )
    parser.add_argument(
        "--skip-docker",
        action="store_true",
        help="Skip Docker operations"
    )
    
    args = parser.parse_args()
    
    print(f"{Colors.BLUE}{'='*50}{Colors.END}")
    print(f"{Colors.BLUE}EpiSPY Deployment Script{Colors.END}")
    print(f"{Colors.BLUE}{'='*50}{Colors.END}\n")
    
    # Check prerequisites
    if not check_prerequisites():
        print_error("Prerequisites check failed")
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        print_error("Environment setup failed")
        sys.exit(1)
    
    # Docker deployment
    if args.mode in ["docker", "full"] and not args.skip_docker:
        if build_docker_images():
            if start_docker_services():
                print_success("Docker deployment completed")
            else:
                print_error("Failed to start Docker services")
                sys.exit(1)
        else:
            print_error("Docker build failed")
            sys.exit(1)
    
    # Local deployment
    if args.mode in ["local", "full"]:
        if not install_dependencies():
            print_error("Dependency installation failed")
            sys.exit(1)
        
        if not initialize_database():
            print_warning("Database initialization failed, continuing...")
    
    # Run tests
    if not args.skip_tests:
        run_tests()
    
    print(f"\n{Colors.GREEN}{'='*50}{Colors.END}")
    print(f"{Colors.GREEN}Deployment completed successfully!{Colors.END}")
    print(f"{Colors.GREEN}{'='*50}{Colors.END}\n")
    
    print("Next steps:")
    print("1. Edit .env file with your configuration")
    print("2. Start the API: python run_api.py")
    print("3. Start the dashboard: streamlit run src/dashboard/Home.py")
    print("4. Check health: curl http://localhost:8000/api/v1/health")


if __name__ == "__main__":
    main()

