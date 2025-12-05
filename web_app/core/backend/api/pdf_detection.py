"""
PDF Detection API endpoints
Provides REST API for PDF component detection with multi-page support.
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

from web_app.core.backend.services.pdf_service import (
    PDFProcessingService,
    PDFDetectionResult,
    PDFPageResult
)

from web_app.core.backend.services.component_service import ComponentDetectionService
from web_app.core.backend.api.component_detection import get_component_service
from web_app.core.backend.utils.config import get_settings
from web_app.core.backend.utils.logging_config import StructuredLogger

logger = logging.getLogger(__name__)
structured_logger = StructuredLogger(__name__)

router = APIRouter()

# Response models
class PDFPageDetection(BaseModel):
    """Single detection within a PDF page"""
    class_name: str
    confidence: float
    bbox: dict
    center: dict
    area: float

class PDFPageResponse(BaseModel):
    """Response for a single PDF page"""
    page_number: int
    image_url: str  # URL to access the page image
    image_dimensions: dict
    processing_time: float
    detections: List[PDFPageDetection]
    total_detections: int

class PDFDetectionResponse(BaseModel):
    """Response for complete PDF detection"""
    success: bool
    message: str
    pdf_path: str
    pdf_id: str  # Unique identifier for this PDF processing session
    total_pages: int
    total_detections: int
    total_processing_time: float
    page_results: List[PDFPageResponse]
    model_info: dict

    model_config = {"protected_namespaces": ()}

def get_pdf_service() -> PDFProcessingService:
    """Get PDF processing service instance"""
    try:
        component_service = get_component_service()
        return PDFProcessingService(component_service)
    except Exception as e:
        logger.error(f"Failed to create PDF service: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"PDF service initialization failed: {e}"
        )

@router.post("/detect", response_model=PDFDetectionResponse)
async def detect_components_in_pdf(
    file: UploadFile = File(..., description="PDF file for component detection"),
    save_visualizations: Optional[bool] = Form(False, description="Save visualization images"),
    pdf_service: PDFProcessingService = Depends(get_pdf_service)
):
    """
    Detect electrical components in all pages of a PDF document.
    
    - **file**: PDF file containing SLD diagrams
    - **save_visualizations**: Whether to save visualization images for each page
    
    Returns detection results for all pages with component information.
    """
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
    # Create temporary file for PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file_path = tmp_file.name
        
        try:
            # Save uploaded file
            content = await file.read()
            tmp_file.write(content)
            tmp_file.flush()
            
            logger.info(f"📄 Processing PDF: {file.filename} ({len(content)} bytes)")
            
            # Process PDF
            pdf_result = await pdf_service.detect_components_in_pdf(
                pdf_path=tmp_file_path,
                save_visualizations=save_visualizations
            )
            
            # Convert to response format
            page_responses = []
            for page_result in pdf_result.page_results:
                # Convert detections
                page_detections = [
                    PDFPageDetection(
                        class_name=det.class_name,
                        confidence=det.confidence,
                        bbox=det.bbox,
                        center=det.center,
                        area=det.area
                    )
                    for det in page_result.detections
                ]
                
                page_response = PDFPageResponse(
                    page_number=page_result.page_number,
                    image_url=page_result.image_url,
                    image_dimensions=page_result.image_dimensions,
                    processing_time=page_result.processing_time,
                    detections=page_detections,
                    total_detections=len(page_detections)
                )
                page_responses.append(page_response)
            
            # Log the detection
            structured_logger.log_component_detection(
                image_path=file.filename,
                detections_count=pdf_result.total_detections,
                processing_time=pdf_result.total_processing_time
            )
            
            response = PDFDetectionResponse(
                success=True,
                message=f"Successfully processed {pdf_result.total_pages} pages with {pdf_result.total_detections} total components",
                pdf_path=file.filename,
                pdf_id=pdf_result.pdf_id,
                total_pages=pdf_result.total_pages,
                total_detections=pdf_result.total_detections,
                total_processing_time=pdf_result.total_processing_time,
                page_results=page_responses,
                model_info=pdf_result.model_info
            )
            
            return response
            
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"PDF processing failed: {str(e)}"
            )
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_file_path)
            except:
                pass

@router.post("/info")
async def get_pdf_info(
    file: UploadFile = File(..., description="PDF file to analyze"),
    pdf_service: PDFProcessingService = Depends(get_pdf_service)
):
    """
    Get information about a PDF file without processing it.
    
    Returns basic PDF metadata and page count.
    """
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file_path = tmp_file.name
        
        try:
            # Save uploaded file
            content = await file.read()
            tmp_file.write(content)
            tmp_file.flush()
            
            # Get PDF info
            pdf_info = pdf_service.get_pdf_info(tmp_file_path)
            
            return {
                "success": True,
                "filename": file.filename,
                "file_size": len(content),
                "pdf_info": pdf_info
            }
            
        except Exception as e:
            logger.error(f"PDF info extraction failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"PDF info extraction failed: {str(e)}"
            )
        
        finally:
            try:
                os.unlink(tmp_file_path)
            except:
                pass

@router.get("/supported-formats")
async def get_supported_formats():
    """Get supported PDF formats and limitations"""
    return {
        "supported_formats": ["pdf"],
        "max_file_size": "10MB",
        "max_pages": 50,  # Reasonable limit for processing
        "recommended_dpi": 300,
        "supported_content": [
            "Single Line Diagrams (SLD)",
            "Electrical schematics",
            "Technical drawings with electrical components"
        ],
        "detected_components": [
            "Ammeter",
            "Cable Termination Box",
            "Earth Electrode",
            "Single Phase Tap-Off Unit",
            "voltmeter"
        ]
    }

@router.get("/{pdf_id}/page/{page_number}/image")
async def get_pdf_page_image(
    pdf_id: str,
    page_number: int
):
    """
    Serve a PDF page image by PDF ID and page number.

    Args:
        pdf_id: Unique identifier for the PDF processing session
        page_number: Page number (1-based)

    Returns:
        FileResponse with the page image
    """
    try:
        # Construct the image path
        uploads_dir = Path(__file__).parent.parent / "uploads" / "pdf_images"
        image_path = uploads_dir / pdf_id / f"page_{page_number:03d}.png"

        # Check if file exists
        if not image_path.exists():
            logger.error(f"PDF page image not found: {image_path}")
            raise HTTPException(
                status_code=404,
                detail=f"PDF page image not found for PDF {pdf_id}, page {page_number}"
            )

        logger.info(f"📷 Serving PDF page image: {image_path}")

        # Return the image file
        return FileResponse(
            path=str(image_path),
            media_type="image/png",
            filename=f"pdf_{pdf_id}_page_{page_number}.png"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve PDF page image: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to serve PDF page image: {str(e)}"
        )
