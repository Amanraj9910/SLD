"""
Component Detection API endpoints
Provides REST API for YOLO-based component detection in SLD diagrams.
"""

import os
import tempfile
import logging
import asyncio
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

from web_app.core.backend.services.component_service import ComponentDetectionService
from web_app.core.backend.services.interactive_html_service import InteractiveHTMLService
from web_app.core.backend.utils.config import get_settings, resolve_model_path
from web_app.core.backend.utils.logging_config import StructuredLogger

# Removed mock service - always use real YOLO model

# Setup logging
logger = logging.getLogger(__name__)
structured_logger = StructuredLogger(__name__)

# Create router
router = APIRouter()

# Pydantic models for request/response
class ComponentDetectionRequest(BaseModel):
    """Request model for component detection"""
    confidence_threshold: Optional[float] = Field(0.03, ge=0.0, le=1.0)
    iou_threshold: Optional[float] = Field(0.45, ge=0.0, le=1.0)
    save_visualization: Optional[bool] = False
    device: Optional[str] = "auto"

class BoundingBox(BaseModel):
    """Bounding box model"""
    x1: int
    y1: int
    x2: int
    y2: int

class ComponentDetection(BaseModel):
    """Individual component detection result"""
    class_name: str
    class_id: int
    confidence: float
    bbox: BoundingBox
    center: dict
    area: int

class ComponentDetectionResponse(BaseModel):
    """Response model for component detection"""
    success: bool
    message: str
    image_path: str
    image_dimensions: dict
    processing_time: float
    detections: List[ComponentDetection]
    model_info: dict
    visualization_url: Optional[str] = None
    interactive_html_url: Optional[str] = None

    model_config = {"protected_namespaces": ()}

class BatchDetectionRequest(BaseModel):
    """Request model for batch detection"""
    file_urls: List[str]
    confidence_threshold: Optional[float] = 0.03
    iou_threshold: Optional[float] = 0.45
    save_visualizations: Optional[bool] = False

class BatchDetectionResponse(BaseModel):
    """Response model for batch detection"""
    success: bool
    message: str
    total_files: int
    successful_detections: int
    failed_detections: int
    results: List[ComponentDetectionResponse]
    processing_time: float

# Global cache for component service (singleton pattern)
_component_service_cache = None
_component_service_error = None

def _initialize_component_service():
    """Initialize component service once at startup"""
    global _component_service_cache, _component_service_error
    
    try:
        logger.info("Initializing component detection service...")
        settings = get_settings()
        model_path = resolve_model_path(settings.yolo_model_path)

        logger.info(f"Using model path: {model_path}")
        
        # Check if model exists
        model_file = Path(model_path)
        if not model_file.exists():
            logger.warning(f"Model file not found at: {model_path}")
            logger.warning(f"Component detection will be unavailable until model is present")
            _component_service_error = f"Model file not found at: {model_path}"
            return

        logger.info(f"Model file verified: {model_path}")

        # Initialize service
        service = ComponentDetectionService(
            model_path=model_path,
            confidence_threshold=settings.yolo_confidence_threshold,
            iou_threshold=settings.yolo_iou_threshold
        )

        # Validate service
        if service.class_names:
            class_count = len(service.class_names)
            logger.info(f"Component service loaded with {class_count} classes")
            _component_service_cache = service
            logger.info("✅ Component detection service ready")
        else:
            logger.warning("Service has no class names - component detection unavailable")
            _component_service_error = "Service has no class names"
            
    except Exception as e:
        logger.warning(f"Could not initialize component detection: {e}")
        _component_service_error = str(e)

# Dependency to get component detection service
def get_component_service() -> ComponentDetectionService:
    """Get component detection service instance (lazy initialization)"""
    global _component_service_cache, _component_service_error
    
    # If not initialized yet, try to initialize
    if _component_service_cache is None and _component_service_error is None:
        _initialize_component_service()
    
    # If there's an error, raise it
    if _component_service_error and _component_service_cache is None:
        logger.error(f"Component service not available: {_component_service_error}")
        raise HTTPException(
            status_code=503,
            detail=f"Component detection service not available: {_component_service_error}"
        )
    
    if _component_service_cache is None:
        logger.error("Component detection service is not initialized")
        raise HTTPException(
            status_code=503,
            detail="Component detection service is not available"
        )
    
    return _component_service_cache

@router.post("/predict", response_model=ComponentDetectionResponse)
async def predict_components(
    file: UploadFile = File(..., description="Image file for component detection"),
    confidence_threshold: Optional[float] = Form(0.03, description="Confidence threshold (0.0-1.0)"),
    iou_threshold: Optional[float] = Form(0.45, description="IoU threshold for NMS (0.0-1.0)"),
    save_visualization: Optional[bool] = Form(False, description="Save visualization image"),
    device: Optional[str] = Form("auto", description="Device for inference (auto, cpu, cuda)"),
    service: ComponentDetectionService = Depends(get_component_service)
):
    """
    Detect electrical components in an SLD image.
    
    - **file**: Image file (JPG, PNG, BMP, TIFF)
    - **confidence_threshold**: Minimum confidence for detections (default: 0.03)
    - **iou_threshold**: IoU threshold for Non-Maximum Suppression (default: 0.45)
    - **save_visualization**: Whether to save visualization image (default: False)
    - **device**: Device for inference - auto, cpu, or cuda (default: auto)
    
    Returns detected components with bounding boxes, confidence scores, and metadata.
    """
    
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image (JPG, PNG, BMP, TIFF)"
            )
        
        # Validate parameters
        if not (0.0 <= confidence_threshold <= 1.0):
            raise HTTPException(
                status_code=400,
                detail="Confidence threshold must be between 0.0 and 1.0"
            )
        
        if not (0.0 <= iou_threshold <= 1.0):
            raise HTTPException(
                status_code=400,
                detail="IoU threshold must be between 0.0 and 1.0"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Update service parameters
            service.confidence_threshold = confidence_threshold
            service.iou_threshold = iou_threshold
            service.device = device
            
            # Run detection
            result = await service.detect_components_async(
                image_path=tmp_file_path,
                save_visualization=save_visualization
            )
            
            # Log the detection
            structured_logger.log_component_detection(
                image_path=file.filename,
                detections_count=len(result.detections),
                processing_time=result.processing_time
            )
            
            # Convert result to response format
            detections = [
                ComponentDetection(
                    class_name=det.class_name,
                    class_id=0,  # Default class_id since our Detection doesn't have it
                    confidence=det.confidence,
                    bbox=BoundingBox(
                        x1=int(det.bbox["x1"]),
                        y1=int(det.bbox["y1"]),
                        x2=int(det.bbox["x2"]),
                        y2=int(det.bbox["y2"])
                    ),
                    center={"x": det.center["x"], "y": det.center["y"]},
                    area=int(det.area)
                )
                for det in result.detections
            ]
            
            # Get visualization URL if saved
            visualization_url = None
            if save_visualization and hasattr(result, 'visualization_path'):
                visualization_url = f"/api/v1/components/visualization/{Path(result.visualization_path).name}"

            # Generate interactive HTML
            interactive_html_url = None
            if len(detections) > 0:  # Only generate if we have detections
                try:
                    html_service = InteractiveHTMLService()

                    # Convert detections to the format expected by HTML service
                    html_detections = []
                    for det in detections:
                        html_detections.append({
                            'class_name': det.class_name,
                            'confidence': det.confidence,
                            'bbox': {
                                'x1': det.bbox.x1,
                                'y1': det.bbox.y1,
                                'x2': det.bbox.x2,
                                'y2': det.bbox.y2
                            },
                            'center': det.center,
                            'area': det.area
                        })

                    # Generate HTML file
                    html_filename = f"{Path(file.filename).stem}_interactive.html"
                    html_output_path = Path("results") / "interactive" / html_filename

                    html_file_path = html_service.generate_interactive_html(
                        image_path=tmp_file_path,
                        detections=html_detections,
                        output_path=str(html_output_path),
                        image_dimensions={
                            "width": result.image_dimensions[0],
                            "height": result.image_dimensions[1]
                        },
                        model_info=result.model_info
                    )

                    interactive_html_url = f"/api/v1/components/interactive/{html_filename}"

                except Exception as e:
                    logger.warning(f"Failed to generate interactive HTML: {e}")
                    # Continue without interactive HTML
            
            response = ComponentDetectionResponse(
                success=True,
                message=f"Successfully detected {len(detections)} components",
                image_path=file.filename,
                image_dimensions={
                    "width": result.image_dimensions["width"],
                    "height": result.image_dimensions["height"]
                },
                processing_time=result.processing_time,
                detections=detections,
                model_info=result.model_info,
                visualization_url=visualization_url,
                interactive_html_url=interactive_html_url
            )
            
            return response
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Component detection failed: {e}", exc_info=True)
        structured_logger.log_error("ComponentDetectionError", str(e), filename=file.filename)
        raise HTTPException(
            status_code=500,
            detail=f"Component detection failed: {str(e)}"
        )

@router.post("/predict-batch", response_model=BatchDetectionResponse)
async def predict_components_batch(
    files: List[UploadFile] = File(..., description="Multiple image files"),
    confidence_threshold: Optional[float] = Form(0.03),
    iou_threshold: Optional[float] = Form(0.45),
    save_visualizations: Optional[bool] = Form(False),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    service: ComponentDetectionService = Depends(get_component_service)
):
    """
    Detect components in multiple images (batch processing).
    
    - **files**: Multiple image files
    - **confidence_threshold**: Minimum confidence for detections
    - **iou_threshold**: IoU threshold for NMS
    - **save_visualizations**: Whether to save visualization images
    
    Returns results for all processed images.
    """
    
    import time
    start_time = time.time()
    
    results = []
    successful_detections = 0
    failed_detections = 0
    
    # Update service parameters
    service.confidence_threshold = confidence_threshold
    service.iou_threshold = iou_threshold
    
    for file in files:
        try:
            # Validate file type
            if not file.content_type.startswith('image/'):
                logger.warning(f"Skipping non-image file: {file.filename}")
                failed_detections += 1
                continue
            
            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
            
            try:
                # Run detection
                result = await service.detect_components_async(
                    image_path=tmp_file_path,
                    save_visualization=save_visualizations
                )
                
                # Convert to response format
                detections = [
                    ComponentDetection(
                        class_name=det.class_name,
                        class_id=0,  # Default class_id
                        confidence=det.confidence,
                        bbox=BoundingBox(
                            x1=int(det.bbox["x1"]),
                            y1=int(det.bbox["y1"]),
                            x2=int(det.bbox["x2"]),
                            y2=int(det.bbox["y2"])
                        ),
                        center={"x": det.center["x"], "y": det.center["y"]},
                        area=int(det.area)
                    )
                    for det in result.detections
                ]
                
                file_result = ComponentDetectionResponse(
                    success=True,
                    message=f"Successfully detected {len(detections)} components",
                    image_path=file.filename,
                    image_dimensions={
                        "width": result.image_dimensions["width"],
                        "height": result.image_dimensions["height"]
                    },
                    processing_time=result.processing_time,
                    detections=detections,
                    model_info=result.model_info
                )
                
                results.append(file_result)
                successful_detections += 1
                
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
                
        except Exception as e:
            logger.error(f"Failed to process {file.filename}: {e}")
            failed_detections += 1
            
            # Add error result
            error_result = ComponentDetectionResponse(
                success=False,
                message=f"Failed to process: {str(e)}",
                image_path=file.filename,
                image_dimensions={"width": 0, "height": 0},
                processing_time=0.0,
                detections=[],
                model_info={}
            )
            results.append(error_result)
    
    total_time = time.time() - start_time
    
    return BatchDetectionResponse(
        success=successful_detections > 0,
        message=f"Processed {len(files)} files: {successful_detections} successful, {failed_detections} failed",
        total_files=len(files),
        successful_detections=successful_detections,
        failed_detections=failed_detections,
        results=results,
        processing_time=total_time
    )

@router.get("/models")
async def get_available_models():
    """Get list of available YOLO models"""
    models_dir = Path("component_detection/models")
    
    if not models_dir.exists():
        return {"models": [], "message": "Models directory not found"}
    
    models = []
    for model_file in models_dir.glob("*.pt"):
        models.append({
            "name": model_file.name,
            "path": str(model_file),
            "size": model_file.stat().st_size,
            "modified": model_file.stat().st_mtime
        })
    
    return {"models": models}

@router.get("/classes")
async def get_component_classes(
    service: ComponentDetectionService = Depends(get_component_service)
):
    """Get list of component classes supported by the model"""
    return {
        "classes": service.class_names,
        "total_classes": len(service.class_names)
    }

@router.get("/visualization/{filename}")
async def get_visualization(filename: str):
    """Get visualization image"""
    viz_path = Path("results") / "visualizations" / filename

    if not viz_path.exists():
        raise HTTPException(status_code=404, detail="Visualization not found")

    return FileResponse(viz_path)

@router.get("/interactive/{filename}")
async def get_interactive_html(filename: str):
    """Get interactive HTML visualization"""
    html_path = Path("results") / "interactive" / filename

    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Interactive HTML not found")

    return FileResponse(html_path, media_type="text/html")

@router.get("/health")
async def health_check(
    service: ComponentDetectionService = Depends(get_component_service)
):
    """Health check for component detection service"""
    try:
        # Test if model is loaded
        model_loaded = service.model is not None
        
        return {
            "status": "healthy" if model_loaded else "unhealthy",
            "model_loaded": model_loaded,
            "model_path": service.model_path,
            "confidence_threshold": service.confidence_threshold,
            "iou_threshold": service.iou_threshold,
            "device": service.device
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
