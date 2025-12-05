"""
Annotation API endpoints
Provides REST API for manual annotation and project management.
"""

import os
import tempfile
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

from web_app.core.backend.services.annotation_service import AnnotationService
from utils.config import get_settings
from utils.logging_config import StructuredLogger

# Setup logging
logger = logging.getLogger(__name__)
structured_logger = StructuredLogger(__name__)

# Create router
router = APIRouter()

# Pydantic models for request/response
class AnnotationModel(BaseModel):
    """Individual annotation model"""
    class_id: int
    class_name: str
    bbox: List[float] = Field(..., min_items=4, max_items=4)  # [x_center, y_center, width, height]
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    annotator: str = "manual"

class CreateProjectRequest(BaseModel):
    """Request model for creating annotation project"""
    project_name: str
    created_by: str = "user"

class ProjectResponse(BaseModel):
    """Response model for annotation project"""
    success: bool
    message: str
    project_name: str
    image_path: str
    image_dimensions: Dict[str, int]
    annotations: List[AnnotationModel]
    class_names: Dict[int, str]
    created_by: str
    last_modified: Optional[str] = None

class AddAnnotationRequest(BaseModel):
    """Request model for adding annotation"""
    class_id: int
    bbox: List[float] = Field(..., min_items=4, max_items=4)
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    annotator: str = "manual"

class UpdateAnnotationRequest(BaseModel):
    """Request model for updating annotation"""
    class_id: Optional[int] = None
    bbox: Optional[List[float]] = Field(None, min_items=4, max_items=4)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

class ValidationResponse(BaseModel):
    """Response model for annotation validation"""
    success: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]

class StatisticsResponse(BaseModel):
    """Response model for annotation statistics"""
    total: int
    by_class: Dict[str, int]
    avg_confidence: float
    classes_used: int
    image_dimensions: List[int]

# Dependency to get annotation service
def get_annotation_service() -> AnnotationService:
    """Get annotation service instance"""
    return AnnotationService()

@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    file: UploadFile = File(..., description="Image file for annotation"),
    project_name: str = Form(..., description="Name of the annotation project"),
    created_by: str = Form("user", description="Name of the project creator"),
    service: AnnotationService = Depends(get_annotation_service)
):
    """
    Create a new annotation project.
    
    - **file**: Image file to annotate (JPG, PNG, BMP, TIFF)
    - **project_name**: Unique name for the project
    - **created_by**: Name of the person creating the project
    
    Returns project information and empty annotation list.
    """
    
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image (JPG, PNG, BMP, TIFF)"
            )
        
        # Save uploaded file
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        file_extension = Path(file.filename).suffix
        image_filename = f"{project_name}_{file.filename}"
        image_path = upload_dir / image_filename
        
        content = await file.read()
        with open(image_path, "wb") as f:
            f.write(content)
        
        # Create project
        project = await service.create_project_async(
            image_path=str(image_path),
            project_name=project_name,
            created_by=created_by
        )
        
        # Log the operation
        structured_logger.log_annotation_operation(
            operation="create_project",
            project_name=project_name,
            annotations_count=0
        )
        
        # Convert to response format
        annotations = [
            AnnotationModel(
                class_id=ann.class_id,
                class_name=ann.class_name,
                bbox=list(ann.bbox),
                confidence=ann.confidence,
                annotator=ann.annotator
            )
            for ann in project.annotations
        ]
        
        response = ProjectResponse(
            success=True,
            message=f"Project '{project_name}' created successfully",
            project_name=project.project_name,
            image_path=project.image_path,
            image_dimensions={
                "width": project.image_dimensions[0],
                "height": project.image_dimensions[1]
            },
            annotations=annotations,
            class_names=project.class_names,
            created_by=project.created_by,
            last_modified=project.last_modified
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create project: {e}", exc_info=True)
        structured_logger.log_error("ProjectCreationError", str(e), project_name=project_name)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create project: {str(e)}"
        )

@router.get("/projects/{project_name}", response_model=ProjectResponse)
async def get_project(
    project_name: str,
    service: AnnotationService = Depends(get_annotation_service)
):
    """
    Get an existing annotation project.
    
    - **project_name**: Name of the project to retrieve
    
    Returns complete project information including annotations.
    """
    
    try:
        project = await service.load_project_async(project_name)
        
        # Convert to response format
        annotations = [
            AnnotationModel(
                class_id=ann.class_id,
                class_name=ann.class_name,
                bbox=list(ann.bbox),
                confidence=ann.confidence,
                annotator=ann.annotator
            )
            for ann in project.annotations
        ]
        
        response = ProjectResponse(
            success=True,
            message=f"Project '{project_name}' loaded successfully",
            project_name=project.project_name,
            image_path=project.image_path,
            image_dimensions={
                "width": project.image_dimensions[0],
                "height": project.image_dimensions[1]
            },
            annotations=annotations,
            class_names=project.class_names,
            created_by=project.created_by,
            last_modified=project.last_modified
        )
        
        return response
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_name}' not found"
        )
    except Exception as e:
        logger.error(f"Failed to load project: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load project: {str(e)}"
        )

@router.post("/projects/{project_name}/annotations")
async def add_annotation(
    project_name: str,
    annotation: AddAnnotationRequest,
    service: AnnotationService = Depends(get_annotation_service)
):
    """
    Add an annotation to a project.
    
    - **project_name**: Name of the project
    - **annotation**: Annotation data (class_id, bbox, confidence)
    
    Returns success message and updated annotation count.
    """
    
    try:
        # Load project
        await service.load_project_async(project_name)
        
        # Add annotation
        await service.add_annotation_async(
            class_id=annotation.class_id,
            bbox=tuple(annotation.bbox),
            confidence=annotation.confidence,
            annotator=annotation.annotator
        )
        
        # Save project
        await service.save_project_async()
        
        # Log the operation
        structured_logger.log_annotation_operation(
            operation="add_annotation",
            project_name=project_name,
            annotations_count=len(service.current_project.annotations)
        )
        
        return {
            "success": True,
            "message": "Annotation added successfully",
            "total_annotations": len(service.current_project.annotations)
        }
        
    except Exception as e:
        logger.error(f"Failed to add annotation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add annotation: {str(e)}"
        )

@router.put("/projects/{project_name}/annotations/{annotation_index}")
async def update_annotation(
    project_name: str,
    annotation_index: int,
    annotation: UpdateAnnotationRequest,
    service: AnnotationService = Depends(get_annotation_service)
):
    """
    Update an existing annotation.
    
    - **project_name**: Name of the project
    - **annotation_index**: Index of the annotation to update
    - **annotation**: Updated annotation data
    
    Returns success message.
    """
    
    try:
        # Load project
        await service.load_project_async(project_name)
        
        # Update annotation
        await service.update_annotation_async(
            index=annotation_index,
            class_id=annotation.class_id,
            bbox=tuple(annotation.bbox) if annotation.bbox else None,
            confidence=annotation.confidence
        )
        
        # Save project
        await service.save_project_async()
        
        return {
            "success": True,
            "message": f"Annotation {annotation_index} updated successfully"
        }
        
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail=f"Annotation {annotation_index} not found"
        )
    except Exception as e:
        logger.error(f"Failed to update annotation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update annotation: {str(e)}"
        )

@router.delete("/projects/{project_name}/annotations/{annotation_index}")
async def delete_annotation(
    project_name: str,
    annotation_index: int,
    service: AnnotationService = Depends(get_annotation_service)
):
    """
    Delete an annotation from a project.
    
    - **project_name**: Name of the project
    - **annotation_index**: Index of the annotation to delete
    
    Returns success message and updated annotation count.
    """
    
    try:
        # Load project
        await service.load_project_async(project_name)
        
        # Delete annotation
        await service.remove_annotation_async(annotation_index)
        
        # Save project
        await service.save_project_async()
        
        return {
            "success": True,
            "message": f"Annotation {annotation_index} deleted successfully",
            "total_annotations": len(service.current_project.annotations)
        }
        
    except IndexError:
        raise HTTPException(
            status_code=404,
            detail=f"Annotation {annotation_index} not found"
        )
    except Exception as e:
        logger.error(f"Failed to delete annotation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete annotation: {str(e)}"
        )

@router.post("/projects/{project_name}/export/yolo")
async def export_yolo(
    project_name: str,
    service: AnnotationService = Depends(get_annotation_service)
):
    """
    Export project annotations in YOLO format.
    
    - **project_name**: Name of the project to export
    
    Returns download links for YOLO format files.
    """
    
    try:
        # Load project
        await service.load_project_async(project_name)
        
        # Export to YOLO format
        output_dir = Path("results") / "exports" / project_name
        await service.export_yolo_format_async(str(output_dir))
        
        return {
            "success": True,
            "message": "YOLO export completed successfully",
            "files": {
                "annotations": f"/api/v1/annotations/exports/{project_name}/{project_name}.txt",
                "classes": f"/api/v1/annotations/exports/{project_name}/classes.txt",
                "image": f"/api/v1/annotations/exports/{project_name}/{Path(service.current_project.image_path).name}"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to export YOLO: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export YOLO: {str(e)}"
        )

@router.get("/projects/{project_name}/validate", response_model=ValidationResponse)
async def validate_project(
    project_name: str,
    service: AnnotationService = Depends(get_annotation_service)
):
    """
    Validate annotations in a project.
    
    - **project_name**: Name of the project to validate
    
    Returns validation results with errors, warnings, and info.
    """
    
    try:
        # Load project
        await service.load_project_async(project_name)
        
        # Validate annotations
        issues = await service.validate_annotations_async()
        
        return ValidationResponse(
            success=len(issues["errors"]) == 0,
            errors=issues["errors"],
            warnings=issues["warnings"],
            info=issues["info"]
        )
        
    except Exception as e:
        logger.error(f"Failed to validate project: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate project: {str(e)}"
        )

@router.get("/projects/{project_name}/statistics", response_model=StatisticsResponse)
async def get_project_statistics(
    project_name: str,
    service: AnnotationService = Depends(get_annotation_service)
):
    """
    Get statistics for a project.
    
    - **project_name**: Name of the project
    
    Returns annotation statistics and metrics.
    """
    
    try:
        # Load project
        await service.load_project_async(project_name)
        
        # Get statistics
        stats = await service.get_statistics_async()
        
        return StatisticsResponse(
            total=stats["total"],
            by_class=stats["by_class"],
            avg_confidence=stats["avg_confidence"],
            classes_used=stats["classes_used"],
            image_dimensions=list(stats["image_dimensions"])
        )
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )

@router.get("/classes")
async def get_component_classes():
    """Get list of available component classes"""
    service = AnnotationService()
    return {
        "classes": service.class_names,
        "total_classes": len(service.class_names)
    }

@router.get("/exports/{project_name}/{filename}")
async def get_export_file(project_name: str, filename: str):
    """Get exported file"""
    file_path = Path("results") / "exports" / project_name / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Export file not found")
    
    return FileResponse(file_path)

@router.get("/health")
async def health_check():
    """Health check for annotation service"""
    try:
        service = AnnotationService()
        
        return {
            "status": "healthy",
            "available_classes": len(service.class_names),
            "project_directory": str(service.project_dir)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
