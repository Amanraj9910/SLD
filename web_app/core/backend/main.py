"""
FastAPI Backend for SLD Processing Application
Provides REST API endpoints for component detection, text detection, and annotation.
"""

import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBearer
import uvicorn
from dotenv import load_dotenv

# Import our modules
from api.component_detection import router as component_router
from api.text_detection import router as text_router
from api.pdf_detection import router as pdf_router
from api.annotation import router as annotation_router
from utils.config import get_settings
from utils.logging_config import setup_logging

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize connection to main text detection module
try:
    from init_text_detection import setup_text_detection_path, test_text_detection_connectivity
    logger.info("🔗 Connecting to main text detection module...")
    text_detection_ready = setup_text_detection_path()
    if text_detection_ready:
        logger.info("✅ Successfully connected to main text detection module")
        logger.info("   Web app backend is now unified with the main text detection system")
    else:
        logger.warning("⚠️  Failed to connect to main text detection module")
        logger.warning("   Text detection features will be unavailable")
except ImportError as e:
    logger.error(f"❌ Text detection initialization module not found: {e}")
    text_detection_ready = False
except Exception as e:
    logger.error(f"❌ Unexpected error during text detection initialization: {e}")
    text_detection_ready = False

# Security
security = HTTPBearer(auto_error=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting SLD Processing Application")
    
    # Create necessary directories
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SLD Processing Application")

# Create FastAPI application
app = FastAPI(
    title="SLD Processing API",
    description="Single Line Diagram Processing with Component Detection, Text Extraction, and Annotation Tools",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Get settings
settings = get_settings()

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

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Serve frontend build files if they exist
frontend_build_path = Path(__file__).parent.parent / "frontend" / "build"
if frontend_build_path.exists():
    logger.info(f"✅ Frontend build found at: {frontend_build_path}")
    app.mount("/frontend", StaticFiles(directory=str(frontend_build_path)), name="frontend")
else:
    logger.warning(f"⚠️  Frontend build not found at: {frontend_build_path}")

# Serve files from main text detection module
main_text_detection_path = Path(r"C:\Users\admin\Downloads\SLD\SLD\text_detection")
if main_text_detection_path.exists():
    app.mount("/text_detection", StaticFiles(directory=str(main_text_detection_path)), name="text_detection")
    logger.info(f"✅ Serving main text detection files from: {main_text_detection_path}")
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

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check text detection connectivity
    text_detection_status = "available" if text_detection_ready else "unavailable"

    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": "2024-07-16T10:00:00Z",
        "services": {
            "backend": "running",
            "component_detection": "available",
            "text_detection": text_detection_status,
            "annotation": "available"
        },
        "text_detection": {
            "module_connected": text_detection_ready,
            "azure_configured": bool(os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')),
            "viewer_available": (text_detection_static_path / "interactive_text_viewer.html").exists() if 'text_detection_static_path' in locals() else False
        }
    }

@app.get("/api/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {
        "message": "API is working!",
        "backend": "running",
        "cors": "enabled"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "SLD Processing API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "component_detection": "/api/v1/components/",
            "text_detection": "/api/v1/text/",
            "annotation": "/api/v1/annotations/"
        }
    }

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
        file_path = Path("uploads") / filename
        
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
    file_path = Path("uploads") / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)

@app.delete("/api/v1/files/{filename}")
async def delete_file(filename: str):
    """Delete uploaded file"""
    file_path = Path("uploads") / filename
    
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
    import psutil
    import platform
    
    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "memory_total": psutil.virtual_memory().total,
        "memory_available": psutil.virtual_memory().available,
        "disk_usage": {
            "total": psutil.disk_usage('/').total,
            "used": psutil.disk_usage('/').used,
            "free": psutil.disk_usage('/').free
        }
    }

@app.get("/api/v1/system/status")
async def system_status():
    """Get system status"""
    import psutil
    
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "uptime": "N/A",  # Would need to track application start time
        "active_connections": len(psutil.net_connections())
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
