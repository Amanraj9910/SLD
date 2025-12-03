"""
Unified startup script - combines app.py and deploy.sh logic
Used when deploy.sh is not found
"""

import sys
import os
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and log output"""
    print(f"\n{'='*60}")
    print(f"📦 {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, shell=True, check=False, capture_output=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    root_dir = Path(__file__).parent.absolute()
    os.chdir(str(root_dir))
    
    print(f"\n{'='*60}")
    print(f"🚀 SLD Backend Startup (Python Entry Point)")
    print(f"{'='*60}")
    print(f"Root: {root_dir}")
    print(f"Python: {sys.version}")
    print(f"{'='*60}\n")
    
    # Step 1: Install dependencies
    print("📥 Installing dependencies...")
    os.system("pip install --upgrade pip setuptools wheel > /dev/null 2>&1")
    os.system("pip install -r requirements.txt 2>&1 | tail -5")
    
    # Step 2: Verify FastAPI
    print("\n✔️  Verifying FastAPI...")
    try:
        import fastapi
        print(f"   FastAPI {fastapi.__version__} ready")
    except ImportError:
        print("   ❌ FastAPI not installed")
        sys.exit(1)
    
    # Step 3: Test import
    print("   Testing app import...")
    backend_dir = root_dir / "web_app" / "core" / "backend"
    sys.path.insert(0, str(backend_dir))
    os.chdir(str(backend_dir))
    
    try:
        from main import app
        print("   ✅ App imported successfully")
    except Exception as e:
        print(f"   ❌ Failed to import app: {e}")
        sys.exit(1)
    
    # Step 4: Start app
    print(f"\n{'='*60}")
    print(f"🎯 Starting FastAPI Backend")
    print(f"{'='*60}\n")
    
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            access_log=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n👋 Shutdown requested")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Failed to start app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
