#!/usr/bin/env python3
"""
SLD Processing Platform - Automated Installation Script
This script will install all Python dependencies and set up the environment.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, description="", check=True):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}")
    print(f"Running: {command}")
    
    try:
        if isinstance(command, str):
            result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        else:
            result = subprocess.run(command, check=check, capture_output=True, text=True)
        
        if result.stdout:
            print(f"✅ Output: {result.stdout.strip()}")
        
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} is not supported. Please install Python 3.8 or higher.")
        sys.exit(1)
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")

def check_pip():
    """Check if pip is available and upgrade it"""
    print("\n📦 Checking pip...")
    
    try:
        import pip
        print("✅ pip is available")
    except ImportError:
        print("❌ pip is not installed. Please install pip first.")
        sys.exit(1)
    
    # Upgrade pip
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], "Upgrading pip")

def install_python_dependencies():
    """Install Python dependencies"""
    print("\n📚 Installing Python dependencies...")
    
    # Check if requirements.txt exists
    req_file = Path("requirements.txt")
    if not req_file.exists():
        print("❌ requirements.txt not found. Please run this script from the SLD directory.")
        sys.exit(1)
    
    # Install requirements
    run_command([
        sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
    ], "Installing Python packages from requirements.txt")

def install_additional_dependencies():
    """Install additional dependencies that might be needed"""
    print("\n🔧 Installing additional dependencies...")
    
    additional_packages = [
        "python-dotenv",
        "python-multipart",
        "aiofiles",
    ]
    
    for package in additional_packages:
        run_command([
            sys.executable, "-m", "pip", "install", package
        ], f"Installing {package}", check=False)

def setup_directories():
    """Create necessary directories"""
    print("\n📁 Setting up directories...")
    
    directories = [
        "uploads",
        "logs", 
        "results",
        "results/visualizations",
        "results/exports",
        "annotation_projects",
        "component_detection/models"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"📁 Directory already exists: {directory}")

def download_yolo_model():
    """Download default YOLO model if not present"""
    print("\n🤖 Checking YOLO model...")
    
    model_path = Path("component_detection/models/yolov8n.pt")
    
    if model_path.exists():
        print("✅ YOLO model already exists")
        return
    
    print("📥 Downloading default YOLO model...")
    
    try:
        import urllib.request
        
        model_url = "https://github.com/ultralytics/assets/releases/download/v8.0.0/yolov8n.pt"
        
        print(f"Downloading from: {model_url}")
        urllib.request.urlretrieve(model_url, model_path)
        print("✅ YOLO model downloaded successfully")
        
    except Exception as e:
        print(f"⚠️ Could not download YOLO model: {e}")
        print("You can download it manually from: https://github.com/ultralytics/assets/releases/download/v8.0.0/yolov8n.pt")

def check_environment_file():
    """Check if .env file exists and is configured"""
    print("\n🔧 Checking environment configuration...")
    
    env_file = Path(".env")
    env_template = Path(".env.template")
    
    if not env_file.exists():
        if env_template.exists():
            print("📋 Copying .env.template to .env")
            import shutil
            shutil.copy(env_template, env_file)
            print("✅ .env file created from template")
        else:
            print("⚠️ No .env file found. Creating basic .env file...")
            with open(env_file, 'w') as f:
                f.write("""# Azure Document Intelligence Configuration
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://sld.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=8n1hs7EHtYI7nKxRvktl9VhoRg3GnKQYYcd1xqMXne2t8avsu9pgJQQJ99BEACYeBjFXJ3w3AAALACOGm7Iv

# Azure AI Foundry Configuration (if needed)
AZURE_AI_FOUNDRY_ENDPOINT=https://ai-diagramanalysis709756132870.openai.azure.com/
AZURE_AI_FOUNDRY_KEY=9oaTfptIYncr9vUe1JegGBXBXVF7VCVXi4pntMJGuUj2C84GxJexJQQJ99BEACYeBjFXJ3w3AAAAACOGvCqX

# Application Configuration
DEBUG=true
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
""")
            print("✅ Basic .env file created")
    else:
        print("✅ .env file already exists")

def test_imports():
    """Test if key packages can be imported"""
    print("\n🧪 Testing package imports...")
    
    test_packages = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("ultralytics", "YOLO"),
        ("cv2", "OpenCV"),
        ("PIL", "Pillow"),
        ("numpy", "NumPy"),
        ("azure.ai.documentintelligence", "Azure Document Intelligence"),
    ]
    
    failed_imports = []
    
    for package, name in test_packages:
        try:
            __import__(package)
            print(f"✅ {name} imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import {name}: {e}")
            failed_imports.append(name)
    
    if failed_imports:
        print(f"\n⚠️ Some packages failed to import: {', '.join(failed_imports)}")
        print("You may need to install them manually or check for compatibility issues.")
    else:
        print("\n🎉 All packages imported successfully!")

def main():
    """Main installation function"""
    print("🚀 SLD Processing Platform - Installation Script")
    print("=" * 50)
    
    # Check current directory
    if not Path("README.md").exists() or not Path("requirements.txt").exists():
        print("❌ Please run this script from the SLD project root directory")
        sys.exit(1)
    
    try:
        # Step 1: Check Python version
        check_python_version()
        
        # Step 2: Check and upgrade pip
        check_pip()
        
        # Step 3: Install Python dependencies
        install_python_dependencies()
        
        # Step 4: Install additional dependencies
        install_additional_dependencies()
        
        # Step 5: Setup directories
        setup_directories()
        
        # Step 6: Download YOLO model
        download_yolo_model()
        
        # Step 7: Check environment file
        check_environment_file()
        
        # Step 8: Test imports
        test_imports()
        
        print("\n" + "=" * 50)
        print("🎉 Installation completed successfully!")
        print("\nNext steps:")
        print("1. Start the backend: cd web_app/backend && python main.py")
        print("2. In another terminal, install frontend dependencies:")
        print("   cd web_app/frontend && npm install")
        print("3. Start the frontend: npm start")
        print("4. Open http://localhost:3000 in your browser")
        print("\n📚 Check README.md for more detailed instructions")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Installation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Installation failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
