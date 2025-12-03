"""
Entry point for Azure App Service deployment
Serves both FastAPI backend and React frontend
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
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import FileResponse
        
        # Serve frontend build
        frontend_build = root_dir / "web_app" / "core" / "frontend" / "build"
        
        # Mount frontend static files
        if frontend_build.exists():
            @app.get("/{full_path:path}")
            async def serve_spa(full_path: str):
                """Serve React SPA with fallback to index.html"""
                # Don't intercept API routes
                if full_path.startswith("api/"):
                    return None
                
                # Check if file exists in build
                file_path = frontend_build / full_path
                if file_path.exists() and file_path.is_file():
                    return FileResponse(str(file_path))
                
                # Fallback to index.html for SPA routing
                index_path = frontend_build / "index.html"
                if index_path.exists():
                    return FileResponse(str(index_path))
                
                return {"error": "Not found"}
        
        import uvicorn
        
        port = int(os.getenv("PORT", 8000))
        print(f"\n{'='*60}")
        print(f"🚀 Starting SLD Application (Backend + Frontend)")
        print(f"   Port: {port}")
        print(f"   Backend: {os.getcwd()}")
        print(f"   Frontend: {frontend_build if frontend_build.exists() else 'NOT FOUND'}")
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
