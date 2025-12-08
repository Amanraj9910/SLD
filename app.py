"""
Entry point for Azure App Service and Docker deployment
Serves the FastAPI backend application
"""

import sys
import os
from pathlib import Path

# Setup Python path - ensure the project root is in sys.path
root_dir = Path(__file__).parent.absolute()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Set PYTHONPATH environment variable for consistency
os.environ['PYTHONPATH'] = str(root_dir)

# Import the FastAPI app from the backend module
# This works because PYTHONPATH is set to project root
try:
    from web_app.core.backend.main import app
    
    # Export for Gunicorn: gunicorn app:app
    __all__ = ['app']
    
except ImportError as e:
    print(f"❌ Failed to import FastAPI app: {e}")
    print(f"   Python path: {sys.path}")
    print(f"   Root directory: {root_dir}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Run with uvicorn when executed directly (for local development)
if __name__ == "__main__":
    try:
        import uvicorn
        
        port = int(os.getenv("PORT", 8000))
        host = os.getenv("HOST", "0.0.0.0")
        
        print(f"\n{'='*60}")
        print(f"🚀 Starting SLD Application")
        print(f"   Host: {host}")
        print(f"   Port: {port}")
        print(f"   Root: {root_dir}")
        print(f"   Python Path: {sys.path[0]}")
        print(f"{'='*60}\n")
        
        uvicorn.run(
            "app:app",
            host=host,
            port=port,
            reload=False,
            access_log=True,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Failed to start app: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
