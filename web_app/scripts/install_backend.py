#!/usr/bin/env python3
"""
Backend Installation Script
Install required Python packages for the SLD Processing Backend
"""

import subprocess
import sys
import os

def run_command(command, description=""):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}")
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False

def main():
    print("🚀 SLD Backend - Installing Python Dependencies")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("❌ Please run this script from the web_app/backend directory")
        sys.exit(1)
    
    # Essential packages for the backend to start
    essential_packages = [
        "pydantic-settings==2.1.0",
        "fastapi==0.105.0", 
        "uvicorn[standard]==0.25.0",
        "python-multipart==0.0.6",
        "python-dotenv==1.0.0",
        "pydantic==2.6.0"
    ]
    
    print("Installing essential packages first...")
    for package in essential_packages:
        success = run_command(
            f"{sys.executable} -m pip install {package}",
            f"Installing {package}"
        )
        if not success:
            print(f"⚠️ Failed to install {package}, but continuing...")
    
    # Try to install all requirements
    requirements_path = "../../requirements.txt"
    if os.path.exists(requirements_path):
        print("\nInstalling all requirements...")
        success = run_command(
            f"{sys.executable} -m pip install -r {requirements_path}",
            "Installing from requirements.txt"
        )
        if not success:
            print("⚠️ Some packages failed to install, but essential ones should work")
    
    print("\n" + "=" * 50)
    print("🎉 Backend installation completed!")
    print("\nNext steps:")
    print("1. Try starting the backend: python main.py")
    print("2. If it fails, install missing packages individually")
    print("3. Check http://localhost:8000/docs when running")

if __name__ == "__main__":
    main()
