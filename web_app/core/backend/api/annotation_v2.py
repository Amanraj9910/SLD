"""
Annotation API v2 — Multi-Image Project Endpoints
Provides REST API for multi-image annotation projects stored on the server.
"""

import io
import json
import logging
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from web_app.core.backend.services.project_manager import (
    ProjectManager,
    get_project_manager,
    sanitize_project_name,
)

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def _validate_image_files(files: List[UploadFile]) -> None:
    """Validate that all uploaded files are acceptable images."""
    for f in files:
        ext = Path(f.filename or "").suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type '{f.filename}'. Only JPG and PNG are allowed.",
            )


# ─── Project Endpoints ────────────────────────────────────────────


@router.get("/v2/projects")
async def list_projects():
    """List all annotation projects on the server."""
    try:
        mgr = get_project_manager()
        projects = mgr.list_projects()
        return {"success": True, "projects": projects, "total": len(projects)}
    except Exception as e:
        logger.error(f"Failed to list projects: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v2/projects")
async def create_project(
    files: List[UploadFile] = File(..., description="Image files (JPG/PNG)"),
    project_name: str = Form(..., description="Display name for the project"),
    created_by: str = Form("user", description="Creator identifier"),
):
    """
    Create a new annotation project with multiple images.

    - Images are renamed sequentially: `<project>_1.jpg`, `<project>_2.png`, …
    - An empty `_annotations.coco.json` is created.
    """
    try:
        _validate_image_files(files)

        sanitized = sanitize_project_name(project_name)
        mgr = get_project_manager()

        # Read all file contents
        file_tuples = []
        for f in files:
            content = await f.read()
            file_tuples.append((f.filename or "image.jpg", content, f.content_type or "image/jpeg"))

        result = mgr.create_project(
            project_name=sanitized,
            display_name=project_name,
            files=file_tuples,
            created_by=created_by,
        )

        return {"success": True, **result}

    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v2/projects/{project_name}")
async def get_project(project_name: str):
    """Get full project details including images and annotations."""
    try:
        mgr = get_project_manager()
        project = mgr.get_project(project_name)
        return {"success": True, **project}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
    except Exception as e:
        logger.error(f"Failed to get project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/v2/projects/{project_name}")
async def delete_project(project_name: str):
    """Delete an entire project and all its files."""
    try:
        mgr = get_project_manager()
        deleted = mgr.delete_project(project_name)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        return {"success": True, "message": f"Project '{project_name}' deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Image Endpoints ──────────────────────────────────────────────


@router.post("/v2/projects/{project_name}/images")
async def add_images(
    project_name: str,
    files: List[UploadFile] = File(..., description="Additional image files"),
):
    """Add more images to an existing project. They continue the sequence."""
    try:
        _validate_image_files(files)
        mgr = get_project_manager()

        file_tuples = []
        for f in files:
            content = await f.read()
            file_tuples.append((f.filename or "image.jpg", content, f.content_type or "image/jpeg"))

        new_images = mgr.add_images(project_name, file_tuples)

        return {
            "success": True,
            "added_count": len(new_images),
            "images": new_images,
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
    except Exception as e:
        logger.error(f"Failed to add images: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v2/projects/{project_name}/images/{sequence}")
async def get_image(project_name: str, sequence: int):
    """Serve an image file by its sequence number."""
    try:
        mgr = get_project_manager()
        
        if mgr.blob_storage.is_active():
            img_bytes = mgr.get_image_bytes(project_name, sequence)
            if img_bytes is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Image {sequence} not found in project '{project_name}'",
                )
            # Find extension from blob listing
            all_blobs = mgr.blob_storage.list_files(prefix=f"{project_name}/images/{project_name}_{sequence}.")
            ext = ".jpg"
            if all_blobs:
                ext = Path(all_blobs[0]).suffix.lower()
            media_type = "image/png" if ext == ".png" else "image/jpeg"
            return StreamingResponse(io.BytesIO(img_bytes), media_type=media_type)

        image_path = mgr.get_image_path(project_name, sequence)

        if not image_path or not image_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Image {sequence} not found in project '{project_name}'",
            )

        # Determine media type
        ext = image_path.suffix.lower()
        media_type = "image/png" if ext == ".png" else "image/jpeg"

        return FileResponse(str(image_path), media_type=media_type)

    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
    except Exception as e:
        logger.error(f"Failed to get image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/v2/projects/{project_name}/images/{sequence}")
async def delete_image(project_name: str, sequence: int):
    """Delete an image and its associated annotations."""
    try:
        mgr = get_project_manager()
        deleted = mgr.delete_image(project_name, sequence)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Image {sequence} not found in project '{project_name}'",
            )
        return {"success": True, "message": f"Image {sequence} deleted"}
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
    except Exception as e:
        logger.error(f"Failed to delete image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Annotation Endpoints ─────────────────────────────────────────


@router.put("/v2/projects/{project_name}/annotations")
async def save_annotations(project_name: str, payload: dict):
    """
    Batch save all annotations for a project.
    Expects JSON body: { "annotations": [...], "categories": [...] }
    """
    try:
        mgr = get_project_manager()
        annotations = payload.get("annotations", [])
        categories = payload.get("categories", [])

        result = mgr.save_annotations(project_name, annotations, categories)
        return result

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
    except Exception as e:
        logger.error(f"Failed to save annotations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v2/projects/{project_name}/annotations")
async def get_annotations(project_name: str):
    """Get all annotations for a project."""
    try:
        mgr = get_project_manager()
        result = mgr.get_annotations(project_name)
        return {"success": True, **result}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
    except Exception as e:
        logger.error(f"Failed to get annotations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Export Endpoints ──────────────────────────────────────────────


@router.get("/v2/projects/{project_name}/export/coco")
async def export_coco_json(project_name: str):
    """Download the _annotations.coco.json file."""
    try:
        mgr = get_project_manager()
        coco_data = mgr.get_coco_json(project_name)

        content = json.dumps(coco_data, indent=2, ensure_ascii=False)
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="_annotations.coco.json"'
            },
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
    except Exception as e:
        logger.error(f"Failed to export COCO: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v2/projects/{project_name}/export/zip")
async def export_project_zip(project_name: str):
    """
    Download the full project as a ZIP file.
    Structure: images/ + _annotations.coco.json
    """
    try:
        mgr = get_project_manager()
        zip_buffer = mgr.get_project_zip_stream(project_name)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{project_name}.zip"'
            },
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
    except Exception as e:
        logger.error(f"Failed to export ZIP: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
