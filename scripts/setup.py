#!/usr/bin/env python3
"""Setup script for epidemic prediction AI system."""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None

def check_requirements():
    """Check if required software is installed."""
    print("🔍 Checking requirements...")
    
    requirements = {
        "python": "python --version",
        "pip": "pip --version",
        "docker": "docker --version",
        "docker-compose": "docker-compose --version"
    }
    
    missing = []
    for name, command in requirements.items():
        result = run_command(command, f"Checking {name}")
        if result is None:
            missing.append(name)
    
    if missing:
        print(f"\n❌ Missing requirements: {', '.join(missing)}")
        print("Please install missing requirements and run setup again.")
        return False
    
    print("✅ All requirements satisfied")
    return True

def setup_virtual_environment():
    """Set up Python virtual environment."""
    if os.path.exists("epidemic_env"):
        print("✅ Virtual environment already exists")
        return True
    
    success = run_command("python -m venv epidemic_env", "Creating virtual environment")
    return success is not None

def activate_and_install_dependencies():
    """Install Python dependencies."""
    if os.name == 'nt':  # Windows
        activate_cmd = "epidemic_env\\Scripts\\activate"
        pip_cmd = "epidemic_env\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        activate_cmd = "source epidemic_env/bin/activate"
        pip_cmd = "epidemic_env/bin/pip"
    
    # Install dependencies
    success = run_command(f"{pip_cmd} install --upgrade pip", "Upgrading pip")
    if success is None:
        return False
    
    success = run_command(f"{pip_cmd} install -r requirements.txt", "Installing Python dependencies")
    return success is not None

def setup_ollama():
    """Set up Ollama and download models."""
    print("\n🤖 Setting up Ollama...")
    
    # Check if Ollama is running
    result = run_command("curl -s http://localhost:11434/api/tags", "Checking Ollama status")
    
    if result is None:
        print("🔄 Starting Ollama service...")
        if os.name == 'nt':  # Windows
            print("Please start Ollama manually on Windows")
            return False
        else:
            # Try to start Ollama (if installed)
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(5)
    
    # Download required models
    models = ["llama3.2", "meditron"]  # Start with smaller models
    
    for model in models:
        print(f"📥 Downloading {model} model...")
        result = run_command(f"ollama pull {model}", f"Downloading {model}")
        if result is None:
            print(f"⚠️  Failed to download {model}. You can download it later.")
    
    return True

def create_environment_file():
    """Create .env file from template."""
    if os.path.exists(".env"):
        print("✅ .env file already exists")
        return True
    
    if not os.path.exists(".env.example"):
        print("❌ .env.example file not found")
        return False
    
    # Copy .env.example to .env
    success = run_command("cp .env.example .env", "Creating .env file")
    
    if success is not None:
        print("⚠️  Please edit .env file with your actual configuration values")
        return True
    
    return False

def create_data_directories():
    """Create necessary data directories."""
    directories = [
        "data/raw",
        "data/processed", 
        "data/models",
        "data/logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        # Create .gitkeep files
        (Path(directory) / ".gitkeep").touch()
    
    print("✅ Data directories created")
    return True

def generate_sample_data():
    """Generate sample data for testing."""
    print("🔄 Generating sample data...")
    
    try:
        # Activate virtual environment and run data generation
        if os.name == 'nt':  # Windows
            python_cmd = "epidemic_env\\Scripts\\python"
        else:  # Unix/Linux/macOS
            python_cmd = "epidemic_env/bin/python"
        
        success = run_command(
            f"{python_cmd} -c 'from src.data.generators.patient_data import PatientDataGenerator; PatientDataGenerator().save_sample_data()'",
            "Generating sample patient data"
        )
        
        return success is not None
        
    except Exception as e:
        print(f"⚠️  Sample data generation failed: {e}")
        return False

def test_api_startup():
    """Test if API can start successfully."""
    print("🔄 Testing API startup...")
    
    try:
        if os.name == 'nt':  # Windows
            python_cmd = "epidemic_env\\Scripts\\python"
        else:  # Unix/Linux/macOS
            python_cmd = "epidemic_env/bin/python"
        
        # Start API in background for a few seconds
        process = subprocess.Popen([
            python_cmd, "-m", "uvicorn", "src.api.main:app", 
            "--host", "127.0.0.1", "--port", "8000"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        
        # Wait a bit for startup
        time.sleep(10)
        
        # Test health endpoint
        result = run_command("curl -s http://127.0.0.1:8000/api/v1/health", "Testing API health")
        
        # Kill the process
        process.terminate()
        process.wait()
        
        if result and "healthy" in result:
            print("✅ API startup test successful")
            return True
        else:
            print("❌ API startup test failed")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Epidemic Prediction AI System Setup")
    print("=" * 50)
    
    setup_steps = [
        ("Check requirements", check_requirements),
        ("Setup virtual environment", setup_virtual_environment),
        ("Install dependencies", activate_and_install_dependencies),
        ("Create environment file", create_environment_file),
        ("Create data directories", create_data_directories),
        ("Generate sample data", generate_sample_data),
        ("Setup Ollama", setup_ollama),
        ("Test API startup", test_api_startup)
    ]
    
    failed_steps = []
    
    for step_name, step_function in setup_steps:
        print(f"\n{'='*20} {step_name} {'='*20}")
        
        try:
            success = step_function()
            if not success:
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ {step_name} failed with exception: {e}")
            failed_steps.append(step_name)
    
    print("\n" + "="*50)
    print("📋 Setup Summary")
    print("="*50)
    
    if failed_steps:
        print(f"❌ Failed steps: {', '.join(failed_steps)}")
        print("\n⚠️  Some setup steps failed. Please review the errors above.")
        print("You may need to:")
        print("- Install missing software (Docker, Ollama, etc.)")
        print("- Configure API keys in .env file")
        print("- Manually download AI models")
    else:
        print("✅ All setup steps completed successfully!")
        print("\n🎉 Your Epidemic Prediction AI System is ready!")
        
        print("\n📖 Next steps:")
        print("1. Edit .env file with your API keys")
        print("2. Start the system:")
        print("   - API: python -m uvicorn src.api.main:app --reload")
        print("   - Dashboard: streamlit run src/dashboard/Home.py")
        print("3. Or use Docker: docker-compose -f docker/docker-compose.yml up")
    
    return len(failed_steps) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
