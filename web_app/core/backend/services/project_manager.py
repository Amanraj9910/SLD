"""
Multi-Image Annotation Project Manager
Handles server-side storage of annotation projects with multiple images.
Each project gets its own directory with sequentially named images and a single COCO JSON.
"""

import io
import json
import logging
import re
import shutil
import threading
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

logger = logging.getLogger(__name__)

# Thread lock for concurrent access to project files
_project_locks: Dict[str, threading.Lock] = {}
_locks_lock = threading.Lock()


def _get_project_lock(project_name: str) -> threading.Lock:
    """Get or create a lock for a specific project."""
    with _locks_lock:
        if project_name not in _project_locks:
            _project_locks[project_name] = threading.Lock()
        return _project_locks[project_name]


def sanitize_project_name(name: str) -> str:
    """
    Sanitize project name to a safe filesystem-friendly format.
    'My SLD Project' → 'my_sld_project'
    """
    # Lowercase
    name = name.lower().strip()
    # Replace spaces, hyphens, dots with underscores
    name = re.sub(r'[\s\-\.]+', '_', name)
    # Remove any non-alphanumeric/underscore characters
    name = re.sub(r'[^a-z0-9_]', '', name)
    # Collapse multiple underscores
    name = re.sub(r'_+', '_', name)
    # Strip leading/trailing underscores
    name = name.strip('_')
    return name or 'untitled_project'


class ProjectManager:
    """
    Manages multi-image annotation projects stored on the server filesystem.

    Directory structure per project:
        annotation_projects/<project_name>/
            ├── project.json                  ← metadata
            ├── images/
            │    ├── <project_name>_1.jpg
            │    ├── <project_name>_2.png
            │    └── ...
            └── _annotations.coco.json        ← single COCO file
    """

    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}

    def __init__(self, base_dir: Optional[str] = None):
        root = Path(__file__).parent.parent.parent.parent.parent  # project root
        self.base_dir = Path(base_dir) if base_dir else root / "annotation_projects"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        from web_app.core.backend.services.blob_storage import get_blob_storage_backend
        self.blob_storage = get_blob_storage_backend()
        self._initializing_registry = False
        logger.info(f"ProjectManager initialized. Base dir: {self.base_dir}")

    # ─── Global Registry ──────────────────────────────────────────

    def _load_registry(self) -> Dict[str, Any]:
        """Load the global project registry. Auto-initializes if missing."""
        if self.blob_storage.is_active():
            if self.blob_storage.file_exists("registry.json"):
                reg_bytes = self.blob_storage.download_file("registry.json")
                if reg_bytes:
                    return json.loads(reg_bytes.decode('utf-8'))
            return self._init_registry()
        
        reg_path = self.base_dir / "registry.json"
        if reg_path.exists():
            return self._read_json(reg_path)
        return self._init_registry()

    def _save_registry(self, registry: Dict[str, Any]) -> None:
        """Save the global project registry."""
        if self.blob_storage.is_active():
            self.blob_storage.upload_file(
                "registry.json",
                json.dumps(registry, indent=2, ensure_ascii=False).encode('utf-8'),
                "application/json"
            )
            return
        self._write_json(self.base_dir / "registry.json", registry)

    def _init_registry(self) -> Dict[str, Any]:
        """Initialize registry by scanning existing projects."""
        if self._initializing_registry:
            return {"global_next_image_id": 1, "project_order": [], "active_project": None}
        self._initializing_registry = True
        max_image_id = 0
        project_order = []
        
        # Scan existing projects to find max image ID
        projects = self.list_projects()
        # Sort by created_at
        projects.sort(key=lambda p: p.get('created_at', ''))
        
        for p in projects:
            project_order.append(p['name'])
            try:
                proj_data = self.get_project(p['name'])
                for img in proj_data.get('images', []):
                    img_id = img.get('id', 0)
                    if img_id > max_image_id:
                        max_image_id = img_id
            except Exception:
                pass
        
        registry = {
            "global_next_image_id": max_image_id + 1,
            "project_order": project_order,
            "active_project": project_order[-1] if project_order else None,
        }
        self._save_registry(registry)
        self._initializing_registry = False
        return registry

    def is_project_locked(self, project_name: str) -> bool:
        """Check if a project is locked (not the active project)."""
        registry = self._load_registry()
        active = registry.get('active_project')
        if active is None:
            return False
        return project_name != active

    # ─── Project CRUD ──────────────────────────────────────────────

    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects with summary metadata."""
        if self.blob_storage.is_active():
            projects = []
            all_blobs = self.blob_storage.list_files(prefix="")
            project_metas = [b for b in all_blobs if b.endswith("/project.json")]
            
            for meta_blob in sorted(project_metas):
                try:
                    parts = meta_blob.split("/")
                    if len(parts) < 2:
                        continue
                    project_name = parts[0]
                    meta_bytes = self.blob_storage.download_file(meta_blob)
                    if not meta_bytes:
                        continue
                    meta = json.loads(meta_bytes.decode('utf-8'))
                    
                    # Count images under {project_name}/images/
                    images_prefix = f"{project_name}/images/"
                    image_count = sum(1 for b in all_blobs if b.startswith(images_prefix))
                    
                    # Count annotations from {project_name}/_annotations.coco.json
                    coco_blob = f"{project_name}/_annotations.coco.json"
                    annotation_count = 0
                    if coco_blob in all_blobs:
                        coco_bytes = self.blob_storage.download_file(coco_blob)
                        if coco_bytes:
                            coco = json.loads(coco_bytes.decode('utf-8'))
                            annotation_count = len(coco.get("annotations", []))
                            
                    projects.append({
                        "name": meta.get("name", project_name),
                        "display_name": meta.get("display_name", project_name),
                        "image_count": image_count,
                        "annotation_count": annotation_count,
                        "created_at": meta.get("created_at", ""),
                        "last_modified": meta.get("last_modified", ""),
                        "created_by": meta.get("created_by", "user"),
                        "locked": self.is_project_locked(meta.get("name", project_name)),
                    })
                except Exception as e:
                    logger.warning(f"Failed to read project blob {meta_blob}: {e}")
                    continue
            return projects

        projects = []
        if not self.base_dir.exists():
            return projects

        for project_dir in sorted(self.base_dir.iterdir()):
            if not project_dir.is_dir():
                continue
            meta_path = project_dir / "project.json"
            if not meta_path.exists():
                continue

            try:
                meta = self._read_json(meta_path)
                images_dir = project_dir / "images"
                image_count = len(list(images_dir.glob("*"))) if images_dir.exists() else 0

                # Count annotations from COCO file
                coco_path = project_dir / "_annotations.coco.json"
                annotation_count = 0
                if coco_path.exists():
                    coco = self._read_json(coco_path)
                    annotation_count = len(coco.get("annotations", []))

                projects.append({
                    "name": meta.get("name", project_dir.name),
                    "display_name": meta.get("display_name", project_dir.name),
                    "image_count": image_count,
                    "annotation_count": annotation_count,
                    "created_at": meta.get("created_at", ""),
                    "last_modified": meta.get("last_modified", ""),
                    "created_by": meta.get("created_by", "user"),
                    "locked": self.is_project_locked(meta.get("name", project_dir.name)),
                })
            except Exception as e:
                logger.warning(f"Failed to read project {project_dir.name}: {e}")
                continue

        return projects

    def create_project(
        self,
        project_name: str,
        display_name: str,
        files: List[Tuple[str, bytes, str]],
        created_by: str = "user",
    ) -> Dict[str, Any]:
        """
        Create a new project with multiple images.

        Args:
            project_name: sanitized project name (used for directory + file prefix)
            display_name: human-readable display name
            files: list of (original_filename, file_bytes, content_type)
            created_by: user identifier

        Returns:
            Project metadata dict with images list
        """
        if self.blob_storage.is_active():
            if self.blob_storage.file_exists(f"{project_name}/project.json"):
                raise ValueError(f"Project '{project_name}' already exists")

            now = datetime.now(timezone.utc).isoformat()
            images_meta = []
            
            registry = self._load_registry()
            start_id = registry.get('global_next_image_id', 1)
            
            for idx, (original_name, content, content_type) in enumerate(files):
                seq = start_id + idx
                ext = Path(original_name).suffix.lower()
                if ext not in self.ALLOWED_EXTENSIONS:
                    ext = '.jpg'

                seq_filename = f"{project_name}_{seq}{ext}"
                blob_path = f"{project_name}/images/{seq_filename}"
                self.blob_storage.upload_file(blob_path, content, content_type)

                try:
                    with Image.open(io.BytesIO(content)) as img:
                        w, h = img.size
                except Exception:
                    w, h = 0, 0

                images_meta.append({
                    "id": seq,
                    "sequence_number": seq,
                    "original_name": original_name,
                    "file_name": seq_filename,
                    "width": w,
                    "height": h,
                    "date_added": now,
                })

            project_meta = {
                "name": project_name,
                "display_name": display_name,
                "created_by": created_by,
                "created_at": now,
                "last_modified": now,
                "next_sequence": start_id + len(files),
                "locked": False,
                "start_image_id": start_id,
            }
            self.blob_storage.upload_file(
                f"{project_name}/project.json",
                json.dumps(project_meta, indent=2, ensure_ascii=False).encode('utf-8'),
                "application/json"
            )

            coco_data = self._build_coco_json(
                project_name=display_name,
                images=images_meta,
                annotations=[],
                categories=[],
                created_at=now,
                created_by=created_by,
            )
            self.blob_storage.upload_file(
                f"{project_name}/_annotations.coco.json",
                json.dumps(coco_data, indent=2, ensure_ascii=False).encode('utf-8'),
                "application/json"
            )
            
            registry['global_next_image_id'] = start_id + len(files)
            registry.setdefault('project_order', []).append(project_name)
            registry['active_project'] = project_name
            self._save_registry(registry)

            logger.info(f"Created project '{project_name}' in Blob Storage with {len(files)} images")
            return {
                **project_meta,
                "images": images_meta,
                "annotation_count": 0,
            }

        project_dir = self.base_dir / project_name
        if project_dir.exists():
            raise ValueError(f"Project '{project_name}' already exists")

        images_dir = project_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now(timezone.utc).isoformat()

        # Save images with sequential naming
        images_meta = []
        registry = self._load_registry()
        start_id = registry.get('global_next_image_id', 1)
        
        for idx, (original_name, content, _content_type) in enumerate(files):
            seq = start_id + idx
            ext = Path(original_name).suffix.lower()
            if ext not in self.ALLOWED_EXTENSIONS:
                ext = '.jpg'  # fallback

            seq_filename = f"{project_name}_{seq}{ext}"
            dest_path = images_dir / seq_filename

            dest_path.write_bytes(content)

            # Get dimensions
            try:
                with Image.open(dest_path) as img:
                    w, h = img.size
            except Exception:
                w, h = 0, 0

            images_meta.append({
                "id": seq,
                "sequence_number": seq,
                "original_name": original_name,
                "file_name": seq_filename,
                "width": w,
                "height": h,
                "date_added": now,
            })

        # Save project metadata
        project_meta = {
            "name": project_name,
            "display_name": display_name,
            "created_by": created_by,
            "created_at": now,
            "last_modified": now,
            "next_sequence": start_id + len(files),
            "locked": False,
            "start_image_id": start_id,
        }
        self._write_json(project_dir / "project.json", project_meta)

        # Create initial COCO JSON
        coco_data = self._build_coco_json(
            project_name=display_name,
            images=images_meta,
            annotations=[],
            categories=[],
            created_at=now,
            created_by=created_by,
        )
        self._write_json(project_dir / "_annotations.coco.json", coco_data)
        
        registry['global_next_image_id'] = start_id + len(files)
        registry.setdefault('project_order', []).append(project_name)
        registry['active_project'] = project_name
        self._save_registry(registry)

        logger.info(f"Created project '{project_name}' with {len(files)} images")

        return {
            **project_meta,
            "images": images_meta,
            "annotation_count": 0,
        }

    def get_project(self, project_name: str) -> Dict[str, Any]:
        """Get full project metadata including images and annotation count."""
        if self.blob_storage.is_active():
            meta_bytes = self.blob_storage.download_file(f"{project_name}/project.json")
            if not meta_bytes:
                raise FileNotFoundError(f"Project '{project_name}' not found")
            meta = json.loads(meta_bytes.decode('utf-8'))

            coco_bytes = self.blob_storage.download_file(f"{project_name}/_annotations.coco.json")
            coco = json.loads(coco_bytes.decode('utf-8')) if coco_bytes else {
                "images": [], "annotations": [], "categories": []
            }

            return {
                **meta,
                "images": coco.get("images", []),
                "annotations": coco.get("annotations", []),
                "categories": coco.get("categories", []),
            }

        project_dir = self._get_project_dir(project_name)
        meta = self._read_json(project_dir / "project.json")

        # Read COCO to get images and annotations
        coco_path = project_dir / "_annotations.coco.json"
        coco = self._read_json(coco_path) if coco_path.exists() else {
            "images": [], "annotations": [], "categories": []
        }

        return {
            **meta,
            "images": coco.get("images", []),
            "annotations": coco.get("annotations", []),
            "categories": coco.get("categories", []),
        }

    def delete_project(self, project_name: str) -> bool:
        """Delete an entire project and all its files."""
        deleted = False
        if self.blob_storage.is_active():
            if not self.blob_storage.file_exists(f"{project_name}/project.json"):
                return False
            lock = _get_project_lock(project_name)
            with lock:
                self.blob_storage.delete_files_with_prefix(f"{project_name}/")
                logger.info(f"Deleted project '{project_name}' from Blob Storage")
                deleted = True
        else:
            project_dir = self.base_dir / project_name
            if not project_dir.exists():
                return False
    
            lock = _get_project_lock(project_name)
            with lock:
                shutil.rmtree(project_dir)
                logger.info(f"Deleted project '{project_name}'")
                deleted = True
                
        if deleted:
            registry = self._load_registry()
            if project_name in registry.get('project_order', []):
                registry['project_order'].remove(project_name)
            if registry.get('active_project') == project_name:
                registry['active_project'] = registry['project_order'][-1] if registry['project_order'] else None
            self._save_registry(registry)
            
        return deleted

    # ─── Image Management ──────────────────────────────────────────

    def add_images(
        self,
        project_name: str,
        files: List[Tuple[str, bytes, str]],
    ) -> List[Dict[str, Any]]:
        """
        Add more images to an existing project.
        Returns metadata of the newly added images.
        """
        if self.is_project_locked(project_name):
            raise PermissionError(f"Project '{project_name}' is locked. Only the latest project accepts new images.")

        if self.blob_storage.is_active():
            meta_bytes = self.blob_storage.download_file(f"{project_name}/project.json")
            if not meta_bytes:
                raise FileNotFoundError(f"Project '{project_name}' not found")
            
            lock = _get_project_lock(project_name)
            with lock:
                meta = json.loads(meta_bytes.decode('utf-8'))
                
                registry = self._load_registry()
                next_seq = registry.get('global_next_image_id', 1)
                
                now = datetime.now(timezone.utc).isoformat()
                new_images = []
                
                for offset, (original_name, content, content_type) in enumerate(files):
                    seq = next_seq + offset
                    ext = Path(original_name).suffix.lower()
                    if ext not in self.ALLOWED_EXTENSIONS:
                        ext = '.jpg'
                    
                    seq_filename = f"{project_name}_{seq}{ext}"
                    blob_path = f"{project_name}/images/{seq_filename}"
                    self.blob_storage.upload_file(blob_path, content, content_type)
                    
                    try:
                        with Image.open(io.BytesIO(content)) as img:
                            w, h = img.size
                    except Exception:
                        w, h = 0, 0
                        
                    new_images.append({
                        "id": seq,
                        "sequence_number": seq,
                        "original_name": original_name,
                        "file_name": seq_filename,
                        "width": w,
                        "height": h,
                        "date_added": now,
                    })
                    
                # Update project metadata
                meta["next_sequence"] = next_seq + len(files)
                meta["last_modified"] = now
                self.blob_storage.upload_file(
                    f"{project_name}/project.json",
                    json.dumps(meta, indent=2, ensure_ascii=False).encode('utf-8'),
                    "application/json"
                )
                
                registry['global_next_image_id'] = next_seq + len(files)
                self._save_registry(registry)
                
                # Update COCO JSON
                coco_blob = f"{project_name}/_annotations.coco.json"
                coco_bytes = self.blob_storage.download_file(coco_blob)
                coco = json.loads(coco_bytes.decode('utf-8')) if coco_bytes else {
                    "info": {}, "images": [], "annotations": [], "categories": [], "licenses": []
                }
                coco["images"].extend(new_images)
                self.blob_storage.upload_file(
                    coco_blob,
                    json.dumps(coco, indent=2, ensure_ascii=False).encode('utf-8'),
                    "application/json"
                )
                
            logger.info(f"Added {len(files)} images to project '{project_name}' in Blob Storage")
            return new_images

        project_dir = self._get_project_dir(project_name)
        images_dir = project_dir / "images"
        lock = _get_project_lock(project_name)

        with lock:
            meta = self._read_json(project_dir / "project.json")

            registry = self._load_registry()
            next_seq = registry.get('global_next_image_id', 1)

            now = datetime.now(timezone.utc).isoformat()
            new_images = []

            for offset, (original_name, content, _ct) in enumerate(files):
                seq = next_seq + offset
                ext = Path(original_name).suffix.lower()
                if ext not in self.ALLOWED_EXTENSIONS:
                    ext = '.jpg'

                seq_filename = f"{project_name}_{seq}{ext}"
                dest_path = images_dir / seq_filename
                dest_path.write_bytes(content)

                try:
                    with Image.open(dest_path) as img:
                        w, h = img.size
                except Exception:
                    w, h = 0, 0

                new_images.append({
                    "id": seq,
                    "sequence_number": seq,
                    "original_name": original_name,
                    "file_name": seq_filename,
                    "width": w,
                    "height": h,
                    "date_added": now,
                })

            # Update project metadata
            meta["next_sequence"] = next_seq + len(files)
            meta["last_modified"] = now
            self._write_json(project_dir / "project.json", meta)
            
            registry['global_next_image_id'] = next_seq + len(files)
            self._save_registry(registry)

            # Update COCO JSON — add new image entries
            coco_path = project_dir / "_annotations.coco.json"
            coco = self._read_json(coco_path) if coco_path.exists() else {
                "info": {}, "images": [], "annotations": [], "categories": [], "licenses": []
            }
            coco["images"].extend(new_images)
            self._write_json(coco_path, coco)

        logger.info(f"Added {len(files)} images to project '{project_name}'")
        return new_images

    def get_image_path(self, project_name: str, sequence: int) -> Optional[Path]:
        """Get the filesystem path of an image by sequence number."""
        project_dir = self._get_project_dir(project_name)
        images_dir = project_dir / "images"

        # Find image matching the sequence number
        pattern = f"{project_name}_{sequence}.*"
        matches = list(images_dir.glob(pattern))
        if matches:
            return matches[0]
        return None

    def get_image_bytes(self, project_name: str, sequence: int) -> Optional[bytes]:
        """Get the raw bytes of an image by sequence number."""
        if self.blob_storage.is_active():
            prefix = f"{project_name}/images/{project_name}_{sequence}."
            all_blobs = self.blob_storage.list_files(prefix=f"{project_name}/images/")
            match = [b for b in all_blobs if Path(b).stem == f"{project_name}_{sequence}"]
            if match:
                return self.blob_storage.download_file(match[0])
            return None

        # Local fallback
        image_path = self.get_image_path(project_name, sequence)
        if image_path and image_path.exists():
            return image_path.read_bytes()
        return None

    def delete_image(self, project_name: str, sequence: int) -> bool:
        """Delete an image and its annotations from the project."""
        if self.is_project_locked(project_name):
            raise PermissionError(f"Project '{project_name}' is locked. Cannot delete images from locked projects.")

        if self.blob_storage.is_active():
            lock = _get_project_lock(project_name)
            with lock:
                # Find and delete the image file from Blob Storage
                prefix = f"{project_name}/images/{project_name}_{sequence}."
                all_blobs = self.blob_storage.list_files(prefix=f"{project_name}/images/")
                match = [b for b in all_blobs if Path(b).stem == f"{project_name}_{sequence}"]
                if not match:
                    return False
                
                self.blob_storage.delete_file(match[0])
                
                # Remove image and its annotations from COCO JSON in Blob Storage
                coco_blob = f"{project_name}/_annotations.coco.json"
                coco_bytes = self.blob_storage.download_file(coco_blob)
                if coco_bytes:
                    coco = json.loads(coco_bytes.decode('utf-8'))
                    coco["images"] = [
                        img for img in coco.get("images", [])
                        if img.get("id") != sequence
                    ]
                    coco["annotations"] = [
                        ann for ann in coco.get("annotations", [])
                        if ann.get("image_id") != sequence
                    ]
                    self.blob_storage.upload_file(
                        coco_blob,
                        json.dumps(coco, indent=2, ensure_ascii=False).encode('utf-8'),
                        "application/json"
                    )
                
                # Update last_modified in project.json
                meta_bytes = self.blob_storage.download_file(f"{project_name}/project.json")
                if meta_bytes:
                    meta = json.loads(meta_bytes.decode('utf-8'))
                    meta["last_modified"] = datetime.now(timezone.utc).isoformat()
                    self.blob_storage.upload_file(
                        f"{project_name}/project.json",
                        json.dumps(meta, indent=2, ensure_ascii=False).encode('utf-8'),
                        "application/json"
                    )
            logger.info(f"Deleted image {sequence} from project '{project_name}' in Blob Storage")
            return True

        project_dir = self._get_project_dir(project_name)
        lock = _get_project_lock(project_name)

        with lock:
            # Find and delete the image file
            image_path = self.get_image_path(project_name, sequence)
            if not image_path or not image_path.exists():
                return False

            image_path.unlink()

            # Remove image and its annotations from COCO JSON
            coco_path = project_dir / "_annotations.coco.json"
            if coco_path.exists():
                coco = self._read_json(coco_path)
                coco["images"] = [
                    img for img in coco.get("images", [])
                    if img.get("id") != sequence
                ]
                coco["annotations"] = [
                    ann for ann in coco.get("annotations", [])
                    if ann.get("image_id") != sequence
                ]
                self._write_json(coco_path, coco)

            # Update last_modified
            meta = self._read_json(project_dir / "project.json")
            meta["last_modified"] = datetime.now(timezone.utc).isoformat()
            self._write_json(project_dir / "project.json", meta)

        logger.info(f"Deleted image {sequence} from project '{project_name}'")
        return True

    # ─── Annotation Management ─────────────────────────────────────

    def save_annotations(
        self,
        project_name: str,
        annotations: List[Dict[str, Any]],
        categories: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Batch save all annotations for a project.
        Replaces existing annotations in the COCO JSON.
        """
        if self.blob_storage.is_active():
            lock = _get_project_lock(project_name)
            with lock:
                coco_blob = f"{project_name}/_annotations.coco.json"
                coco_bytes = self.blob_storage.download_file(coco_blob)
                coco = json.loads(coco_bytes.decode('utf-8')) if coco_bytes else {
                    "info": {}, "images": [], "annotations": [], "categories": [], "licenses": []
                }
                
                coco["annotations"] = annotations
                coco["categories"] = categories
                self.blob_storage.upload_file(
                    coco_blob,
                    json.dumps(coco, indent=2, ensure_ascii=False).encode('utf-8'),
                    "application/json"
                )
                
                # Update last_modified in project.json
                meta_bytes = self.blob_storage.download_file(f"{project_name}/project.json")
                if meta_bytes:
                    meta = json.loads(meta_bytes.decode('utf-8'))
                    meta["last_modified"] = datetime.now(timezone.utc).isoformat()
                    self.blob_storage.upload_file(
                        f"{project_name}/project.json",
                        json.dumps(meta, indent=2, ensure_ascii=False).encode('utf-8'),
                        "application/json"
                    )
            return {
                "success": True,
                "annotation_count": len(annotations),
                "category_count": len(categories),
            }

        project_dir = self._get_project_dir(project_name)
        lock = _get_project_lock(project_name)

        with lock:
            coco_path = project_dir / "_annotations.coco.json"
            coco = self._read_json(coco_path) if coco_path.exists() else {
                "info": {}, "images": [], "annotations": [], "categories": [], "licenses": []
            }

            coco["annotations"] = annotations
            coco["categories"] = categories
            self._write_json(coco_path, coco)

            # Update last_modified
            meta = self._read_json(project_dir / "project.json")
            meta["last_modified"] = datetime.now(timezone.utc).isoformat()
            self._write_json(project_dir / "project.json", meta)

        return {
            "success": True,
            "annotation_count": len(annotations),
            "category_count": len(categories),
        }

    def get_annotations(self, project_name: str) -> Dict[str, Any]:
        """Get all annotations and categories for a project."""
        if self.blob_storage.is_active():
            coco_blob = f"{project_name}/_annotations.coco.json"
            coco_bytes = self.blob_storage.download_file(coco_blob)
            if not coco_bytes:
                return {"annotations": [], "categories": []}
            coco = json.loads(coco_bytes.decode('utf-8'))
            return {
                "annotations": coco.get("annotations", []),
                "categories": coco.get("categories", []),
            }

        project_dir = self._get_project_dir(project_name)
        coco_path = project_dir / "_annotations.coco.json"

        if not coco_path.exists():
            return {"annotations": [], "categories": []}

        coco = self._read_json(coco_path)
        return {
            "annotations": coco.get("annotations", []),
            "categories": coco.get("categories", []),
        }

    # ─── Export ─────────────────────────────────────────────────────

    def get_coco_json(self, project_name: str) -> Dict[str, Any]:
        """Get the full COCO JSON for export."""
        if self.blob_storage.is_active():
            coco_blob = f"{project_name}/_annotations.coco.json"
            coco_bytes = self.blob_storage.download_file(coco_blob)
            if not coco_bytes:
                raise FileNotFoundError(f"COCO file not found in Blob Storage for project '{project_name}'")
            return json.loads(coco_bytes.decode('utf-8'))

        project_dir = self._get_project_dir(project_name)
        coco_path = project_dir / "_annotations.coco.json"
        if not coco_path.exists():
            raise FileNotFoundError(f"COCO file not found for project '{project_name}'")
        return self._read_json(coco_path)

    def get_project_dir_path(self, project_name: str) -> Path:
        """Get the project directory path for ZIP export."""
        return self._get_project_dir(project_name)

    def get_project_zip_stream(self, project_name: str) -> io.BytesIO:
        """Build the full project ZIP in memory and return it as a stream."""
        if self.blob_storage.is_active():
            # Check if project exists by looking for project.json
            if not self.blob_storage.file_exists(f"{project_name}/project.json"):
                raise FileNotFoundError(f"Project '{project_name}' not found")

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                # 1. Download and add COCO JSON
                coco_blob = f"{project_name}/_annotations.coco.json"
                coco_bytes = self.blob_storage.download_file(coco_blob)
                if coco_bytes:
                    zf.writestr("_annotations.coco.json", coco_bytes)

                # 2. List all images and add them
                all_blobs = self.blob_storage.list_files(prefix=f"{project_name}/images/")
                for blob in sorted(all_blobs):
                    img_bytes = self.blob_storage.download_file(blob)
                    if img_bytes:
                        filename = Path(blob).name
                        zf.writestr(f"images/{filename}", img_bytes)

            zip_buffer.seek(0)
            return zip_buffer

        # Local fallback
        project_dir = self._get_project_dir(project_name)
        images_dir = project_dir / "images"
        coco_path = project_dir / "_annotations.coco.json"

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            if images_dir.exists():
                for img_file in sorted(images_dir.iterdir()):
                    if img_file.is_file():
                        zf.write(img_file, f"images/{img_file.name}")

            if coco_path.exists():
                zf.write(coco_path, "_annotations.coco.json")

        zip_buffer.seek(0)
        return zip_buffer

    # ─── Merge & Validation ────────────────────────────────────────

    def validate_merge_data(self, images: List[Dict], annotations: List[Dict], categories: List[Dict]) -> List[str]:
        """Validate merged data for duplicates. Returns list of error messages."""
        errors = []
        
        # 1. Image ID uniqueness check
        image_ids = [img['id'] for img in images]
        seen_img_ids = set()
        for img_id in image_ids:
            if img_id in seen_img_ids:
                errors.append(f"DUPLICATE IMAGE ID: Image ID {img_id} appears more than once.")
            seen_img_ids.add(img_id)
        
        # 2. Annotation ID uniqueness check
        ann_ids = [ann['id'] for ann in annotations]
        seen_ann_ids = set()
        for ann_id in ann_ids:
            if ann_id in seen_ann_ids:
                errors.append(f"DUPLICATE ANNOTATION ID: Annotation ID {ann_id} appears more than once.")
            seen_ann_ids.add(ann_id)
        
        # 3. Category ID uniqueness check
        cat_ids = [cat['id'] for cat in categories]
        seen_cat_ids = set()
        for cat_id in cat_ids:
            if cat_id in seen_cat_ids:
                errors.append(f"DUPLICATE CATEGORY ID: Category ID {cat_id} appears more than once.")
            seen_cat_ids.add(cat_id)
        
        # 4. Category name uniqueness check
        cat_names = [cat['name'].lower().strip() for cat in categories]
        seen_cat_names = set()
        for name in cat_names:
            if name in seen_cat_names:
                errors.append(f"DUPLICATE CATEGORY NAME: Category '{name}' appears more than once.")
            seen_cat_names.add(name)
        
        # 5. Referential integrity: annotation.image_id must exist in images
        valid_img_ids = set(img['id'] for img in images)
        for ann in annotations:
            if ann.get('image_id') not in valid_img_ids:
                errors.append(f"ORPHAN ANNOTATION: Annotation ID {ann['id']} references non-existent image ID {ann.get('image_id')}.")
        
        # 6. Referential integrity: annotation.category_id must exist in categories
        valid_cat_ids = set(cat['id'] for cat in categories)
        for ann in annotations:
            if ann.get('category_id') not in valid_cat_ids:
                errors.append(f"INVALID CATEGORY: Annotation ID {ann['id']} references non-existent category ID {ann.get('category_id')}.")
        
        return errors

    def merge_projects(self, project_names: List[str]) -> Dict[str, Any]:
        """
        Merge multiple projects into a single COCO JSON.
        Projects are ordered by creation date (earliest first).
        Categories are deduplicated by name (case-insensitive).
        Annotation IDs are re-indexed sequentially (1, 2, 3, ...).
        
        Returns dict with 'coco_data' and 'errors' (validation errors).
        """
        # Load all projects and sort by created_at
        project_data = []
        for name in project_names:
            try:
                proj = self.get_project(name)
                meta_data = {}
                if self.blob_storage.is_active():
                    meta_bytes = self.blob_storage.download_file(f"{name}/project.json")
                    if meta_bytes:
                        meta_data = json.loads(meta_bytes.decode('utf-8'))
                else:
                    project_dir = self.base_dir / name
                    meta_path = project_dir / "project.json"
                    if meta_path.exists():
                        meta_data = self._read_json(meta_path)
                project_data.append({
                    'name': name,
                    'project': proj,
                    'created_at': meta_data.get('created_at', ''),
                })
            except FileNotFoundError:
                raise ValueError(f"Project '{name}' not found")
        
        # Sort by creation date (earliest first)
        project_data.sort(key=lambda p: p['created_at'])
        
        # Collect all images (IDs are already globally unique)
        all_images = []
        all_annotations = []
        
        # Deduplicate categories by name (case-insensitive)
        merged_categories = []
        cat_name_to_id = {}  # lowercase name -> new category id
        next_cat_id = 1
        
        for pd in project_data:
            proj = pd['project']
            
            # Add images directly (already globally unique IDs)
            all_images.extend(proj.get('images', []))
            
            # Process categories
            local_cat_map = {}  # old cat id -> new cat id for this project
            for cat in proj.get('categories', []):
                cat_name_lower = cat['name'].lower().strip()
                if cat_name_lower in cat_name_to_id:
                    # Category already exists, map old ID to existing new ID
                    local_cat_map[cat['id']] = cat_name_to_id[cat_name_lower]
                else:
                    # New category
                    local_cat_map[cat['id']] = next_cat_id
                    cat_name_to_id[cat_name_lower] = next_cat_id
                    merged_categories.append({
                        'id': next_cat_id,
                        'name': cat['name'],
                        'supercategory': cat.get('supercategory', 'none'),
                    })
                    next_cat_id += 1
            
            # Process annotations - remap category IDs
            for ann in proj.get('annotations', []):
                new_ann = dict(ann)
                old_cat_id = ann.get('category_id')
                if old_cat_id in local_cat_map:
                    new_ann['category_id'] = local_cat_map[old_cat_id]
                all_annotations.append(new_ann)
        
        # Re-index annotation IDs sequentially (1, 2, 3, ...)
        for idx, ann in enumerate(all_annotations, start=1):
            ann['id'] = idx
        
        # Run validation
        errors = self.validate_merge_data(all_images, all_annotations, merged_categories)
        
        # Build merged COCO JSON
        now = datetime.now(timezone.utc).isoformat()
        coco_data = {
            'info': {
                'description': f"Merged from: {', '.join(p['name'] for p in project_data)}",
                'version': '1.0',
                'date_created': now,
                'contributor': 'merged',
            },
            'licenses': [],
            'images': all_images,
            'annotations': all_annotations,
            'categories': merged_categories,
        }
        
        return {
            'coco_data': coco_data,
            'errors': errors,
            'summary': {
                'total_images': len(all_images),
                'total_annotations': len(all_annotations),
                'total_categories': len(merged_categories),
                'projects_merged': [p['name'] for p in project_data],
            }
        }

    def get_merged_zip_stream(self, project_names: List[str]) -> Tuple[io.BytesIO, List[str]]:
        """
        Build a merged ZIP with all images from selected projects + merged COCO JSON.
        Returns (zip_buffer, validation_errors).
        """
        merge_result = self.merge_projects(project_names)
        errors = merge_result['errors']
        
        if errors:
            return None, errors
        
        coco_data = merge_result['coco_data']
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add merged COCO JSON
            zf.writestr(
                '_annotations.coco.json',
                json.dumps(coco_data, indent=2, ensure_ascii=False)
            )
            
            # Add images from each project
            project_names_to_fetch = [p['name'] if isinstance(p, dict) else p for p in merge_result['summary']['projects_merged']]
            for name in project_names_to_fetch:
                if self.blob_storage.is_active():
                    all_blobs = self.blob_storage.list_files(prefix=f"{name}/images/")
                    for blob in sorted(all_blobs):
                        img_bytes = self.blob_storage.download_file(blob)
                        if img_bytes:
                            filename = Path(blob).name
                            zf.writestr(f"images/{filename}", img_bytes)
                else:
                    project_dir = self.base_dir / name
                    images_dir = project_dir / "images"
                    if images_dir.exists():
                        for img_file in sorted(images_dir.iterdir()):
                            if img_file.is_file():
                                zf.write(img_file, f"images/{img_file.name}")
        
        zip_buffer.seek(0)
        return zip_buffer, errors

    # ─── Internal Helpers ──────────────────────────────────────────

    def _get_project_dir(self, project_name: str) -> Path:
        """Get project directory, raise if not found."""
        project_dir = self.base_dir / project_name
        if not project_dir.exists():
            raise FileNotFoundError(f"Project '{project_name}' not found")
        return project_dir

    def _get_max_sequence(self, images_dir: Path, project_name: str) -> int:
        """Find the highest sequence number among existing images."""
        max_seq = 0
        if not images_dir.exists():
            return max_seq

        prefix = f"{project_name}_"
        for f in images_dir.iterdir():
            if f.is_file() and f.stem.startswith(prefix):
                suffix = f.stem[len(prefix):]
                if suffix.isdigit():
                    max_seq = max(max_seq, int(suffix))
        return max_seq

    def _build_coco_json(
        self,
        project_name: str,
        images: List[Dict],
        annotations: List[Dict],
        categories: List[Dict],
        created_at: str = "",
        created_by: str = "user",
    ) -> Dict[str, Any]:
        """Build a standard COCO-format JSON structure."""
        return {
            "info": {
                "description": project_name,
                "version": "1.0",
                "date_created": created_at or datetime.now(timezone.utc).isoformat(),
                "contributor": created_by,
            },
            "licenses": [],
            "images": images,
            "annotations": annotations,
            "categories": categories,
        }

    @staticmethod
    def _read_json(path: Path) -> Dict[str, Any]:
        """Read a JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def _write_json(path: Path, data: Dict[str, Any]) -> None:
        """Write a JSON file with pretty formatting."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# Singleton
_manager_instance: Optional[ProjectManager] = None


def get_project_manager() -> ProjectManager:
    """Get singleton ProjectManager instance."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ProjectManager()
    return _manager_instance
