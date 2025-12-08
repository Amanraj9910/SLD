"""
Entry point for Azure App Service and Docker deployment
Serves the FastAPI backend application
"""

import sys
import os
from pathlib import Path

# Setup Python path
root_dir = Path(__file__).parent.absolute()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

os.environ['PYTHONPATH'] = str(root_dir)

# Import FastAPI app
try:
    from web_app.core.backend.main import app
    __all__ = ['app']
except ImportError as e:
    print(f"❌ Failed to import FastAPI app: {e}")
    print(f"   Python path: {sys.path}")
    print(f"   Root directory: {root_dir}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


# =====================================
# Serve React Frontend Build
# =====================================
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Mount static files (JS/CSS)
app.mount(
    "/static",
    StaticFiles(directory="web_app/core/frontend/build/static"),
    name="static"
)

# Route for frontend UI
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    index_path = Path("web_app/core/frontend/build/index.html")
    if index_path.exists():
        return index_path.read_text()
    return HTMLResponse("<h1>Frontend build not found</h1>", status_code=404)


# =====================================
# Uvicorn Local Run
# =====================================
if __name__ == "__main__":
    try:
        import uvicorn
        port = int(os.getenv("PORT", 8000))
        host = os.getenv("HOST", "0.0.0.0")
        
        print("\nRunning local dev server...\n")
        
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
