"""
Entry point for Azure App Service deployment
This file ensures App Service recognizes and runs the Python FastAPI backend
"""

import sys
import os
from pathlib import Path

# Get root directory
root_dir = Path(__file__).parent.absolute()

# Add paths
sys.path.insert(0, str(root_dir))
backend_dir = root_dir / "web_app" / "core" / "backend"
sys.path.insert(0, str(backend_dir))

# Change working directory to backend so relative imports work
os.chdir(str(backend_dir))

# Now import the app
if __name__ == "__main__":
    try:
        from main import app
        import uvicorn
        
        port = int(os.getenv("PORT", 8000))
        print(f"\n{'='*60}")
        print(f"🚀 Starting SLD FastAPI Backend")
        print(f"   Port: {port}")
        print(f"   Working Directory: {os.getcwd()}")
        print(f"   Root: {root_dir}")
        print(f"{'='*60}\n")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            access_log=True,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Failed to start app: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
