"""
Text Detection API endpoints
Provides REST API for Azure Document Intelligence OCR in SLD diagrams.
"""

import os
import tempfile
import logging
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from web_app.core.backend.services.text_service import TextDetectionService
from web_app.core.backend.utils.config import get_settings, resolve_text_detection_path
from web_app.core.backend.utils.logging_config import StructuredLogger

# REMOVED: Mock service has been eliminated to ensure only real Azure API responses are used
# All text detection now requires proper Azure Document Intelligence configuration

# Setup logging
logger = logging.getLogger(__name__)
structured_logger = StructuredLogger(__name__)

# Create router
router = APIRouter()

# Pydantic models for request/response
class TextDetectionRequest(BaseModel):
    """Request model for text detection"""
    output_format: Optional[str] = Field("detailed", pattern="^(detailed|simple)$")

class TextElement(BaseModel):
    """Individual text element model"""
    text: str
    confidence: float
    polygon: List[List[float]]  # List of [x, y] coordinates
    bounding_box: Dict[str, float]  # {"left": x, "top": y, "width": w, "height": h}
    page_number: int = 1

class TextDetectionResponse(BaseModel):
    """Response model for text detection"""
    success: bool
    message: str
    document_path: str
    document_type: str  # "image" or "pdf"
    page_count: int
    processing_time: float
    total_text_length: int
    text_elements: List[TextElement]
    image_dimensions: Optional[Dict[str, int]] = None
    service_info: Dict[str, str]

class BatchTextDetectionRequest(BaseModel):
    """Request model for batch text detection"""
    file_urls: List[str]
    output_format: Optional[str] = "detailed"

class BatchTextDetectionResponse(BaseModel):
    """Response model for batch text detection"""
    success: bool
    message: str
    total_files: int
    successful_detections: int
    failed_detections: int
    results: List[TextDetectionResponse]
    processing_time: float

# Dependency to get text detection service
def get_text_service() -> TextDetectionService:
    """Get text detection service instance - requires proper Azure configuration"""
    try:
        settings = get_settings()

        # Validate that Azure credentials are properly configured
        if not settings.azure_document_intelligence_endpoint or not settings.azure_document_intelligence_key:
            raise ValueError(
                "Azure Document Intelligence credentials are not configured. "
                "Please set AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_KEY "
                "environment variables."
            )

        return TextDetectionService(
            endpoint=settings.azure_document_intelligence_endpoint,
            api_key=settings.azure_document_intelligence_key
        )
    except Exception as e:
        logger.error(f"Failed to initialize text service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Text detection service unavailable: {str(e)}. Please configure Azure Document Intelligence credentials."
        )

@router.post("/extract", response_model=TextDetectionResponse)
async def extract_text(
    file: UploadFile = File(..., description="Document file for text extraction"),
    output_format: Optional[str] = Form("detailed", description="Output format (detailed or simple)"),
    save_results: Optional[bool] = Form(True, description="Save results to JSON file"),
    service: TextDetectionService = Depends(get_text_service)
):
    """
    Extract text from an SLD document using Azure Document Intelligence.

    - **file**: Document file (JPG, PNG, PDF, BMP, TIFF)
    - **output_format**: Output format - detailed (with polygons) or simple (text only)
    - **save_results**: Save results to JSON file for interactive visualization

    Returns extracted text elements with bounding boxes, confidence scores, and metadata.
    The JSON file will be saved in the uploads directory and can be used for interactive visualization.
    """
    
    try:
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/bmp', 'image/tiff', 'application/pdf']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type not supported. Allowed: {', '.join(allowed_types)}"
            )
        
        # Validate output format
        if output_format not in ["detailed", "simple"]:
            raise HTTPException(
                status_code=400,
                detail="Output format must be 'detailed' or 'simple'"
            )
        
        # Save uploaded file to main text detection module directory
        settings = get_settings()
        main_text_detection_path = Path(resolve_text_detection_path(settings.text_detection_path))
        uploads_dir = main_text_detection_path / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)

        # Create unique filename
        import uuid
        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
        tmp_file_path = uploads_dir / unique_filename

        content = await file.read()
        with open(tmp_file_path, 'wb') as f:
            f.write(content)

        tmp_file_path = str(tmp_file_path)
        
        try:
            # Set up output directory for results in main text detection module
            output_dir = None
            if save_results:
                # Save results to main text detection module directory
                settings = get_settings()
                main_text_detection_path = Path(resolve_text_detection_path(settings.text_detection_path))
                output_dir = main_text_detection_path / "outputs" / "web_app_results"
                output_dir.mkdir(parents=True, exist_ok=True)

            # Run text extraction
            result = await service.extract_text_async(
                document_path=tmp_file_path,
                output_format=output_format,
                save_results=save_results,
                output_dir=str(output_dir) if output_dir else None
            )
            
            # Log the extraction
            structured_logger.log_text_detection(
                document_path=file.filename,
                text_elements_count=len(result.text_elements),
                processing_time=result.processing_time
            )
            
            # Convert result to response format
            text_elements = [
                TextElement(
                    text=elem.text,
                    confidence=elem.confidence,
                    polygon=elem.polygon,
                    bounding_box=elem.bounding_box,
                    page_number=elem.page_number
                )
                for elem in result.text_elements
            ]
            
            response = TextDetectionResponse(
                success=True,
                message=f"Successfully extracted {len(text_elements)} text elements",
                document_path=file.filename,
                document_type=result.document_type,
                page_count=result.page_count,
                processing_time=result.processing_time,
                total_text_length=result.total_text_length,
                text_elements=text_elements,
                image_dimensions=result.image_dimensions,
                service_info=result.service_info
            )
            
            return response
            
        finally:
            # Clean up uploaded file (keep results in main text detection module)
            try:
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
                    logger.debug(f"Cleaned up uploaded file: {tmp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up uploaded file {tmp_file_path}: {e}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text extraction failed: {e}", exc_info=True)
        structured_logger.log_error("TextExtractionError", str(e), file_name=file.filename)
        raise HTTPException(
            status_code=500,
            detail=f"Text extraction failed: {str(e)}"
        )

@router.post("/extract-batch", response_model=BatchTextDetectionResponse)
async def extract_text_batch(
    files: List[UploadFile] = File(..., description="Multiple document files"),
    output_format: Optional[str] = Form("detailed"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    service: TextDetectionService = Depends(get_text_service)
):
    """
    Extract text from multiple documents (batch processing).
    
    - **files**: Multiple document files
    - **output_format**: Output format for all files
    
    Returns results for all processed documents.
    """
    
    import time
    start_time = time.time()
    
    results = []
    successful_detections = 0
    failed_detections = 0
    
    for file in files:
        try:
            # Validate file type
            allowed_types = ['image/jpeg', 'image/png', 'image/bmp', 'image/tiff', 'application/pdf']
            if file.content_type not in allowed_types:
                logger.warning(f"Skipping unsupported file: {file.filename}")
                failed_detections += 1
                continue
            
            # Save file temporarily
            file_extension = Path(file.filename).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
            
            try:
                # Run text extraction
                result = await service.extract_text_async(
                    document_path=tmp_file_path,
                    output_format=output_format
                )
                
                # Convert to response format
                text_elements = [
                    TextElement(
                        text=elem.text,
                        confidence=elem.confidence,
                        polygon=elem.polygon,
                        bounding_box=elem.bounding_box,
                        page_number=elem.page_number
                    )
                    for elem in result.text_elements
                ]
                
                file_result = TextDetectionResponse(
                    success=True,
                    message=f"Successfully extracted {len(text_elements)} text elements",
                    document_path=file.filename,
                    document_type=result.document_type,
                    page_count=result.page_count,
                    processing_time=result.processing_time,
                    total_text_length=result.total_text_length,
                    text_elements=text_elements,
                    image_dimensions=result.image_dimensions,
                    service_info=result.service_info
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
            error_result = TextDetectionResponse(
                success=False,
                message=f"Failed to process: {str(e)}",
                document_path=file.filename,
                document_type="unknown",
                page_count=0,
                processing_time=0.0,
                total_text_length=0,
                text_elements=[],
                service_info={}
            )
            results.append(error_result)
    
    total_time = time.time() - start_time
    
    return BatchTextDetectionResponse(
        success=successful_detections > 0,
        message=f"Processed {len(files)} files: {successful_detections} successful, {failed_detections} failed",
        total_files=len(files),
        successful_detections=successful_detections,
        failed_detections=failed_detections,
        results=results,
        processing_time=total_time
    )

@router.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported document formats"""
    return {
        "image_formats": ["JPG", "JPEG", "PNG", "BMP", "TIFF"],
        "document_formats": ["PDF"],
        "content_types": [
            "image/jpeg",
            "image/png", 
            "image/bmp",
            "image/tiff",
            "application/pdf"
        ]
    }

@router.get("/service-info")
async def get_service_info(
    service: TextDetectionService = Depends(get_text_service)
):
    """Get Azure Document Intelligence service information"""
    return service.get_service_info()

@router.post("/test-connection")
async def test_azure_connection(
    service: TextDetectionService = Depends(get_text_service)
):
    """Test connection to Azure Document Intelligence service"""
    try:
        is_connected = await service.test_connection_async()
        
        return {
            "success": is_connected,
            "message": "Connection successful" if is_connected else "Connection failed",
            "service": "Azure Document Intelligence",
            "endpoint": service.endpoint
        }
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}",
            "service": "Azure Document Intelligence",
            "endpoint": service.endpoint
        }

@router.get("/health")
async def health_check(
    service: TextDetectionService = Depends(get_text_service)
):
    """Health check for text detection service"""
    try:
        # Test if service is configured
        is_configured = service.endpoint and service.api_key
        
        # Test connection if configured
        connection_ok = False
        if is_configured:
            try:
                connection_ok = await service.test_connection_async()
            except Exception:
                connection_ok = False
        
        status = "healthy" if is_configured and connection_ok else "unhealthy"
        
        return {
            "status": status,
            "configured": is_configured,
            "connection_ok": connection_ok,
            "endpoint": service.endpoint if service.endpoint else "Not configured",
            "model_id": service.model_id
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
