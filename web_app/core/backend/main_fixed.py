"""
Fixed version of main.py with enhanced error handling and stability improvements.
This file serves as a backup/alternative main entry point for the SLD backend.
"""

import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import FastAPI and dependencies
try:
    from fastapi import FastAPI, HTTPException, UploadFile, File, Form
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import JSONResponse, FileResponse
    import uvicorn
except ImportError as e:
    print(f"Error importing FastAPI dependencies: {e}")
    print("Please install required packages: pip install fastapi uvicorn python-multipart")
    sys.exit(1)

# Import local modules with error handling
try:
    from utils.logging_config import setup_logging
    from utils.config import get_settings
except ImportError as e:
    print(f"Warning: Could not import utils: {e}")
    # Fallback logging setup
    logging.basicConfig(level=logging.INFO)

# Setup logging
logger = logging.getLogger(__name__)

# Initialize settings
try:
    settings = get_settings()
except Exception as e:
    logger.warning(f"Could not load settings: {e}")
    # Fallback settings
    class FallbackSettings:
        debug = True
        api_host = "0.0.0.0"
        api_port = 8000
    settings = FallbackSettings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with enhanced error handling."""
    logger.info("🚀 Starting SLD Processing Application (Fixed Version)")
    
    # Startup
    try:
        # Initialize services
        logger.info("Initializing services...")
        
        # Create necessary directories
        os.makedirs("uploads", exist_ok=True)
        os.makedirs("results", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs("static", exist_ok=True)
        
        logger.info("✅ Application startup complete")
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise
    
    yield
    
    # Shutdown
    try:
        logger.info("🛑 Shutting down SLD Processing Application")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

# Create FastAPI app
app = FastAPI(
    title="SLD Processing Platform (Fixed)",
    description="Enhanced Single Line Diagram Processing Platform with improved stability",
    version="1.0.1",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Enhanced health check with system status."""
    try:
        return {
            "status": "healthy",
            "version": "1.0.1-fixed",
            "timestamp": str(Path(__file__).stat().st_mtime),
            "services": {
                "backend": "running",
                "file_system": "accessible" if os.path.exists("uploads") else "error"
            }
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with enhanced information."""
    return {
        "message": "SLD Processing Platform (Fixed Version)",
        "version": "1.0.1",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "component_detection": "/api/component-detection/detect",
            "text_detection": "/api/text-detection/extract"
        }
    }

# Import API routes with error handling
try:
    from api.component_detection import router as component_router
    app.include_router(component_router, prefix="/api/component-detection", tags=["Component Detection"])
    logger.info("✅ Component detection API loaded")
except ImportError as e:
    logger.warning(f"⚠️ Could not load component detection API: {e}")

try:
    from api.text_detection import router as text_router
    app.include_router(text_router, prefix="/api/text-detection", tags=["Text Detection"])
    logger.info("✅ Text detection API loaded")
except ImportError as e:
    logger.warning(f"⚠️ Could not load text detection API: {e}")

try:
    from api.annotation import router as annotation_router
    app.include_router(annotation_router, prefix="/api/annotation", tags=["Annotation"])
    logger.info("✅ Annotation API loaded")
except ImportError as e:
    logger.warning(f"⚠️ Could not load annotation API: {e}")

# Mount static files
try:
    if os.path.exists("static"):
        app.mount("/static", StaticFiles(directory="static"), name="static")
        logger.info("✅ Static files mounted")
except Exception as e:
    logger.warning(f"⚠️ Could not mount static files: {e}")

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for better error reporting."""
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.debug else "An error occurred",
            "type": type(exc).__name__
        }
    )

if __name__ == "__main__":
    logger.info("🚀 Starting SLD Platform (Fixed Version)")
    logger.info(f"📡 Server will run on http://{settings.api_host}:{settings.api_port}")
    logger.info(f"📖 API Documentation: http://{settings.api_host}:{settings.api_port}/docs")
    
    try:
        uvicorn.run(
            "main_fixed:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=settings.debug,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        sys.exit(1)
