"""
Annotation API v2 — Multi-Image Project Endpoints
Provides REST API for multi-image annotation projects stored on the server.
"""

import asyncio
import io
import json
import logging
import time
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

from web_app.core.backend.services.project_manager import (
    ProjectManager,
    get_project_manager,
    sanitize_project_name,
)

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

class MergeRequest(BaseModel):
    project_names: List[str]


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


# ─── Merge Endpoints ───────────────────────────────────────────

@router.post("/v2/projects/merge/preview")
async def merge_preview(request: MergeRequest):
    """Preview merge result without generating files."""
    try:
        if len(request.project_names) < 2:
            raise HTTPException(status_code=400, detail="Select at least 2 projects to merge.")
        
        mgr = get_project_manager()
        result = mgr.merge_projects(request.project_names)
        
        return {
            "success": len(result['errors']) == 0,
            "summary": result['summary'],
            "errors": result['errors'],
            "categories": result['coco_data']['categories'],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to preview merge: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v2/projects/merge/coco")
async def merge_coco(request: MergeRequest):
    """Download merged COCO JSON."""
    try:
        if len(request.project_names) < 2:
            raise HTTPException(status_code=400, detail="Select at least 2 projects to merge.")
        
        mgr = get_project_manager()
        result = mgr.merge_projects(request.project_names)
        
        if result['errors']:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Validation failed. Cannot export with errors.",
                    "errors": result['errors']
                }
            )
        
        content = json.dumps(result['coco_data'], indent=2, ensure_ascii=False)
        filename = f"merged_{'_'.join(request.project_names)}.json"
        
        return StreamingResponse(
            io.BytesIO(content.encode('utf-8')),
            media_type='application/json',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to merge COCO: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v2/projects/merge/zip")
async def merge_zip(request: MergeRequest):
    """Download merged ZIP (images + COCO JSON)."""
    try:
        if len(request.project_names) < 2:
            raise HTTPException(status_code=400, detail="Select at least 2 projects to merge.")
        
        mgr = get_project_manager()
        zip_buffer, errors = mgr.get_merged_zip_stream(request.project_names)
        
        if errors:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Validation failed. Cannot export with errors.",
                    "errors": errors
                }
            )
        
        filename = f"merged_{'_'.join(request.project_names)}.zip"
        
        return StreamingResponse(
            zip_buffer,
            media_type='application/zip',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to merge ZIP: {e}", exc_info=True)
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

    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
    except Exception as e:
        logger.error(f"Failed to add images: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v2/projects/{project_name}/images/{sequence}/thumb")
async def get_image_thumbnail(
    project_name: str, sequence: int, max_edge: int = 200
):
    """Serve a resized thumbnail for lazy-loaded gallery."""
    try:
        mgr = get_project_manager()
        max_edge = max(64, min(max_edge, 512))
        thumb_bytes = mgr.get_image_thumbnail_bytes(project_name, sequence, max_edge=max_edge)
        if not thumb_bytes:
            raise HTTPException(
                status_code=404,
                detail=f"Image {sequence} not found in project '{project_name}'",
            )
        return StreamingResponse(
            io.BytesIO(thumb_bytes),
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=86400"},
        )
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
    except Exception as e:
        logger.error(f"Failed to get thumbnail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v2/projects/{project_name}/images/{sequence}")
async def get_image(project_name: str, sequence: int):
    """Serve an image file by its sequence number."""
    try:
        mgr = get_project_manager()
        
        if mgr.blob_storage.is_active():
            img_bytes = None
            media_type = "image/jpeg"
            for ext, mime in ((".png", "image/png"), (".jpg", "image/jpeg"), (".jpeg", "image/jpeg")):
                blob_name = f"{project_name}/images/{project_name}_{sequence}{ext}"
                if mgr.blob_storage.file_exists(blob_name):
                    img_bytes = mgr.blob_storage.download_file(blob_name)
                    media_type = mime
                    break
            if img_bytes is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Image {sequence} not found in project '{project_name}'",
                )
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
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
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


def _export_storage_context(mgr: ProjectManager, project_name: str) -> dict:
    """Build diagnostic context for export logging."""
    ctx: dict = {
        "project_name": project_name,
        "storage": "azure_blob" if mgr.blob_storage.is_active() else "local",
    }
    if mgr.blob_storage.is_active():
        ctx["coco_blob"] = f"{project_name}/_annotations.coco.json"
        ctx["coco_exists"] = mgr.blob_storage.file_exists(ctx["coco_blob"])
        ctx["project_json_exists"] = mgr.blob_storage.file_exists(f"{project_name}/project.json")
    else:
        try:
            project_dir = mgr.get_project_dir_path(project_name)
            ctx["project_dir"] = str(project_dir)
            ctx["project_dir_exists"] = project_dir.exists()
            ctx["coco_path"] = str(project_dir / "_annotations.coco.json")
            ctx["coco_exists"] = (project_dir / "_annotations.coco.json").exists()
            images_dir = project_dir / "images"
            ctx["images_dir"] = str(images_dir)
            ctx["images_dir_exists"] = images_dir.exists()
            if images_dir.exists():
                ctx["image_file_count"] = sum(1 for f in images_dir.iterdir() if f.is_file())
        except FileNotFoundError as e:
            ctx["project_dir_error"] = str(e)
    return ctx


@router.get("/v2/projects/{project_name}/export/coco")
async def export_coco_json(project_name: str):
    """Download the _annotations.coco.json file."""
    ctx = {}
    try:
        mgr = get_project_manager()
        ctx = _export_storage_context(mgr, project_name)
        logger.info("COCO export started: %s", ctx)

        raw_coco = mgr.get_coco_json(project_name)
        coco_data = mgr.prepare_coco_for_export(raw_coco)

        # Run validation but don't block export for single projects
        errors = mgr.validate_merge_data(
            coco_data.get('images', []),
            coco_data.get('annotations', []),
            coco_data.get('categories', [])
        )
        if errors:
            logger.warning(
                "COCO export validation warnings for '%s' (%d issues): %s",
                project_name, len(errors), errors,
            )

        content = json.dumps(coco_data, indent=2, ensure_ascii=False)
        logger.info(
            "COCO export succeeded for '%s': bytes=%d images=%d annotations=%d categories=%d",
            project_name,
            len(content.encode("utf-8")),
            len(coco_data.get('images', [])),
            len(coco_data.get('annotations', [])),
            len(coco_data.get('categories', [])),
        )
        safe_name = project_name.replace('"', '')
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_name}_annotations.coco.json"',
                "Content-Length": str(len(content.encode("utf-8"))),
            },
        )

    except FileNotFoundError as e:
        logger.error(
            "COCO export 404 for '%s': %s | context=%s",
            project_name, e, ctx,
        )
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "COCO export 500 for '%s': %s | context=%s",
            project_name, e, ctx, exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v2/projects/{project_name}/export/zip")
async def export_project_zip(project_name: str):
    """
    Download the full project as a ZIP file.
    Structure: images/ + _annotations.coco.json
    """
    ctx = {}
    try:
        mgr = get_project_manager()
        ctx = _export_storage_context(mgr, project_name)
        logger.info("ZIP export started: %s", ctx)

        t0 = time.perf_counter()
        raw_coco = mgr.get_coco_json(project_name)
        coco_data = mgr.prepare_coco_for_export(raw_coco)
        image_count = len(coco_data.get("images", []))
        logger.info(
            "ZIP export '%s': %d images (merge validation skipped for single-project export)",
            project_name,
            image_count,
        )

        zip_buffer, images_added, images_skipped = await asyncio.to_thread(
            mgr.build_export_zip_buffer, project_name, coco_data
        )
        build_secs = time.perf_counter() - t0
        zip_size = zip_buffer.getbuffer().nbytes
        logger.info(
            "ZIP export succeeded for '%s': total=%.2fs zip_bytes=%d images_added=%d images_skipped=%d",
            project_name, build_secs, zip_size, images_added, images_skipped,
        )
        if images_added == 0:
            logger.warning(
                "ZIP export for '%s' contains COCO only — no images were packaged",
                project_name,
            )

        safe_zip_name = project_name.replace('"', '')
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_zip_name}.zip"',
                "Content-Length": str(zip_size),
            },
        )

    except FileNotFoundError as e:
        logger.error(
            "ZIP export 404 for '%s': %s | context=%s",
            project_name, e, ctx,
        )
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "ZIP export 500 for '%s': %s | context=%s",
            project_name, e, ctx, exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))
