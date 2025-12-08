"""
FastAPI Backend for SLD Processing Application
Provides REST API endpoints for component detection, text detection, and annotation.
"""

import os
import logging
import threading
import time
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBearer
import uvicorn
from dotenv import load_dotenv

# Import our modules
from web_app.core.backend.api.component_detection import router as component_router
from web_app.core.backend.api.text_detection import router as text_router
from web_app.core.backend.api.pdf_detection import router as pdf_router
from web_app.core.backend.api.annotation import router as annotation_router
from web_app.core.backend.utils.config import get_settings
from web_app.core.backend.utils.logging_config import setup_logging

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Add exception hook to catch any unhandled exceptions
def _exception_hook(exc_type, exc_value, exc_traceback):
    """Global exception hook to catch unhandled exceptions"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error(
        "❌ UNHANDLED EXCEPTION",
        exc_info=(exc_type, exc_value, exc_traceback)
    )

import sys
sys.excepthook = _exception_hook

# Initialize connection to main text detection module (soft dependency)
# Make this non-blocking - app should start even if text_detection is unavailable
text_detection_ready = False
try:
    from web_app.core.backend.init_text_detection import setup_text_detection_path, test_text_detection_connectivity
    logger.info("🔗 Connecting to main text detection module...")
    text_detection_ready = setup_text_detection_path()
    if text_detection_ready:
        logger.info("✅ Successfully connected to main text detection module")
        logger.info("   Web app backend is now unified with the main text detection system")
    else:
        logger.info("ℹ️  Text detection module not available - feature will be disabled")
        logger.info("   This is normal if text_detection folder is not present")
except ImportError as e:
    logger.info(f"ℹ️  Text detection initialization module not found: {e}")
    logger.info("   Text detection features will be unavailable")
except Exception as e:
    logger.warning(f"⚠️  Could not initialize text detection: {e}")
    logger.info("   Application will continue without text detection features")

# Security
security = HTTPBearer(auto_error=False)

# Get settings FIRST (before using in lifespan)
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("=" * 60)
    logger.info("Starting SLD Processing Application")
    logger.info("=" * 60)
    
    try:
        # Create necessary directories
        # Use project root for consistency (in Docker /app, locally project root)
        root_dir = Path(__file__).parent.parent.parent.parent
        upload_dir = root_dir / settings.upload_folder
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        logs_dir = root_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        results_dir = root_dir / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("✅ Directories created")
        logger.info("✅ Application ready to serve requests")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}", exc_info=True)
        logger.error("Application will continue with limited functionality")
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("Shutting down SLD Processing Application")
    logger.info("=" * 60)

# Create FastAPI application
app = FastAPI(
    title="SLD Processing API",
    description="Single Line Diagram Processing with Component Detection, Text Extraction, and Annotation Tools",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(
    component_router,
    prefix="/api/v1/components",
    tags=["Component Detection"]
)

app.include_router(
    text_router,
    prefix="/api/v1/text",
    tags=["Text Detection"]
)

app.include_router(
    pdf_router,
    prefix="/api/v1/pdf",
    tags=["PDF Detection"]
)

app.include_router(
    annotation_router,
    prefix="/api/v1/annotations",
    tags=["Annotation Tool"]
)

# Serve static files (only mount if directories exist)
# First, try to mount frontend build static files
frontend_static_dir = Path(__file__).parent.parent / "frontend" / "build" / "static"
if frontend_static_dir.exists():
    logger.info(f"✅ Mounting frontend static files from: {frontend_static_dir}")
    app.mount("/static", StaticFiles(directory=str(frontend_static_dir)), name="static")
else:
    # Fallback to backend static directory
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    else:
        logger.warning(f"⚠️  Static directory not found: {static_dir}")
        static_dir.mkdir(parents=True, exist_ok=True)
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

root_dir = Path(__file__).parent.parent.parent.parent
uploads_dir = root_dir / settings.upload_folder

if uploads_dir.exists():
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")
else:
    logger.warning(f"⚠️  Uploads directory not found: {uploads_dir}")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Serve frontend build files if they exist
frontend_build_path = Path(__file__).parent.parent / "frontend" / "build"
if frontend_build_path.exists():
    logger.info(f"✅ Frontend build found at: {frontend_build_path}")
    app.mount("/frontend", StaticFiles(directory=str(frontend_build_path)), name="frontend")
else:
    logger.warning(f"⚠️  Frontend build not found at: {frontend_build_path}")

# Serve files from main text detection module
# Use environment variable or fallback to relative path for cross-platform compatibility
text_detection_env_path = os.getenv('TEXT_DETECTION_PATH')
if text_detection_env_path:
    main_text_detection_path = Path(text_detection_env_path)
else:
    # Fallback: try relative paths that work on both Windows and Linux
    possible_paths = [
        Path(__file__).parent.parent.parent.parent / "text_detection", # Project root (Correct)
        Path(__file__).parent.parent.parent.parent.parent / "text_detection",  # Project root (Legacy/Nested)
        Path("/home/site/wwwroot/text_detection"),  # Azure App Service
        Path(__file__).parent / "text_detection",  # Same directory
    ]
    main_text_detection_path = None
    for p in possible_paths:
        if p.exists():
            main_text_detection_path = p
            break
    if main_text_detection_path is None:
        main_text_detection_path = possible_paths[0]  # Use first as default

# Also define text_detection_static_path for use in health check
text_detection_static_path = main_text_detection_path

if main_text_detection_path.exists():
    try:
        app.mount("/text_detection", StaticFiles(directory=str(main_text_detection_path)), name="text_detection")
        logger.info(f"✅ Serving main text detection files from: {main_text_detection_path}")
    except Exception as e:
        logger.warning(f"⚠️  Could not mount text detection files: {e}")
else:
    logger.warning(f"⚠️  Main text detection path not found: {main_text_detection_path}")

# Serve the interactive text viewer from main module
@app.get("/text_detection_viewer.html")
async def serve_text_viewer():
    """Serve the interactive text detection viewer from main module"""
    viewer_path = main_text_detection_path / "interactive_text_viewer.html"
    if viewer_path.exists():
        logger.info(f"Serving interactive viewer from main module: {viewer_path}")
        return FileResponse(str(viewer_path))
    else:
        logger.error(f"Interactive text viewer not found at: {viewer_path}")
        raise HTTPException(status_code=404, detail="Interactive text viewer not found in main module")

# Serve frontend index.html as SPA fallback
@app.get("/app")
@app.get("/app/{path:path}")
async def serve_frontend(path: str = ""):
    """Serve frontend for all routes under /app"""
    index_path = frontend_build_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    raise HTTPException(status_code=404, detail="Frontend not found")

# Health check endpoint - MUST ALWAYS RETURN 200 OK
@app.get("/health")
async def health_check():
    """Health check endpoint - minimal, non-blocking"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {
        "message": "API is working!",
        "backend": "running",
        "cors": "enabled"
    }

# Root endpoint - Serve React Frontend
@app.get("/")
async def root():
    """Root endpoint - serves React frontend"""
    from fastapi.responses import FileResponse
    index_path = frontend_build_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path), media_type="text/html")
    return JSONResponse(
        status_code=404,
        content={"error": "Frontend not found"}
    )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "type": type(exc).__name__
        }
    )

# File upload validation
async def validate_file_upload(file: UploadFile) -> UploadFile:
    """Validate uploaded file"""
    # Check file size
    max_size = settings.max_file_size
    if file.size and file.size > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {max_size / 1024 / 1024:.1f}MB"
        )
    
    # Check file extension
    allowed_extensions = settings.allowed_extensions
    file_extension = Path(file.filename).suffix.lower().lstrip('.')
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Supported: {', '.join(allowed_extensions)}"
        )
    
    return file

# File management endpoints
@app.post("/api/v1/upload")
async def upload_file(
    file: UploadFile = File(...),
    validated_file: UploadFile = Depends(validate_file_upload)
):
    """Upload a file to the server"""
    try:
        # Generate unique filename
        import uuid
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        file_extension = Path(file.filename).suffix
        
        filename = f"{timestamp}_{unique_id}{file_extension}"
        root_dir = Path(__file__).parent.parent.parent.parent
        file_path = root_dir / settings.upload_folder / filename
        
        # Save file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"File uploaded: {filename}")
        
        return {
            "filename": filename,
            "original_filename": file.filename,
            "size": len(content),
            "content_type": file.content_type,
            "upload_path": str(file_path),
            "url": f"/uploads/{filename}"
        }
        
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/v1/files/{filename}")
async def get_file(filename: str):
    """Get uploaded file"""
    root_dir = Path(__file__).parent.parent.parent.parent
    file_path = root_dir / settings.upload_folder / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)

@app.delete("/api/v1/files/{filename}")
async def delete_file(filename: str):
    """Delete uploaded file"""
    root_dir = Path(__file__).parent.parent.parent.parent
    file_path = root_dir / settings.upload_folder / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        file_path.unlink()
        logger.info(f"File deleted: {filename}")
        return {"message": f"File {filename} deleted successfully"}
    except Exception as e:
        logger.error(f"File deletion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

# System information endpoints
@app.get("/api/v1/system/info")
async def system_info():
    """Get system information"""
    try:
        import psutil
        import platform
        
        # Get disk path based on OS (Windows uses C:, Linux uses /)
        disk_path = 'C:/' if platform.system() == 'Windows' else '/'
        
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "disk_usage": {
                "total": psutil.disk_usage(disk_path).total,
                "used": psutil.disk_usage(disk_path).used,
                "free": psutil.disk_usage(disk_path).free
            }
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {
            "error": "Could not retrieve system information",
            "message": str(e)
        }

@app.get("/api/v1/system/status")
async def system_status():
    """Get system status"""
    try:
        import psutil
        import platform
        
        # Get disk path based on OS
        disk_path = 'C:/' if platform.system() == 'Windows' else '/'
        
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage(disk_path).percent,
            "uptime": "N/A",
            "active_connections": len(psutil.net_connections()) if hasattr(psutil, 'net_connections') else 0
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {
            "error": "Could not retrieve system status",
            "message": str(e)
        }

# Configuration endpoints
@app.get("/api/v1/config")
async def get_config():
    """Get application configuration (public settings only)"""
    return {
        "max_file_size": settings.max_file_size,
        "allowed_extensions": settings.allowed_extensions,
        "yolo_confidence_threshold": settings.yolo_confidence_threshold,
        "yolo_iou_threshold": settings.yolo_iou_threshold,
        "api_version": "1.0.0",
        "features": {
            "component_detection": True,
            "text_detection": True,
            "annotation_tool": True,
            "batch_processing": True
        }
    }

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.api_workers,
        log_level=settings.log_level.lower(),
        access_log=True
    )
