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
        logger.info(f"ProjectManager initialized. Base dir: {self.base_dir}")

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
            
            for idx, (original_name, content, content_type) in enumerate(files, start=1):
                ext = Path(original_name).suffix.lower()
                if ext not in self.ALLOWED_EXTENSIONS:
                    ext = '.jpg'

                seq_filename = f"{project_name}_{idx}{ext}"
                blob_path = f"{project_name}/images/{seq_filename}"
                self.blob_storage.upload_file(blob_path, content, content_type)

                try:
                    with Image.open(io.BytesIO(content)) as img:
                        w, h = img.size
                except Exception:
                    w, h = 0, 0

                images_meta.append({
                    "id": idx,
                    "sequence_number": idx,
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
                "next_sequence": len(files) + 1,
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
        for idx, (original_name, content, _content_type) in enumerate(files, start=1):
            ext = Path(original_name).suffix.lower()
            if ext not in self.ALLOWED_EXTENSIONS:
                ext = '.jpg'  # fallback

            seq_filename = f"{project_name}_{idx}{ext}"
            dest_path = images_dir / seq_filename

            dest_path.write_bytes(content)

            # Get dimensions
            try:
                with Image.open(dest_path) as img:
                    w, h = img.size
            except Exception:
                w, h = 0, 0

            images_meta.append({
                "id": idx,
                "sequence_number": idx,
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
            "next_sequence": len(files) + 1,
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
        if self.blob_storage.is_active():
            if not self.blob_storage.file_exists(f"{project_name}/project.json"):
                return False
            lock = _get_project_lock(project_name)
            with lock:
                self.blob_storage.delete_files_with_prefix(f"{project_name}/")
                logger.info(f"Deleted project '{project_name}' from Blob Storage")
                return True

        project_dir = self.base_dir / project_name
        if not project_dir.exists():
            return False

        lock = _get_project_lock(project_name)
        with lock:
            shutil.rmtree(project_dir)
            logger.info(f"Deleted project '{project_name}'")
            return True

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
        if self.blob_storage.is_active():
            meta_bytes = self.blob_storage.download_file(f"{project_name}/project.json")
            if not meta_bytes:
                raise FileNotFoundError(f"Project '{project_name}' not found")
            
            lock = _get_project_lock(project_name)
            with lock:
                meta = json.loads(meta_bytes.decode('utf-8'))
                next_seq = meta.get("next_sequence", 1)
                
                # Check maximum sequence by listing files under images
                all_blobs = self.blob_storage.list_files(prefix=f"{project_name}/images/")
                existing_max = 0
                prefix = f"{project_name}/images/{project_name}_"
                for b in all_blobs:
                    if b.startswith(prefix):
                        stem = Path(b).stem
                        suffix = stem[len(f"{project_name}_"):]
                        if suffix.isdigit():
                            existing_max = max(existing_max, int(suffix))
                
                next_seq = max(next_seq, existing_max + 1)
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
            next_seq = meta.get("next_sequence", 1)

            # Also check filesystem for highest existing sequence
            existing_max = self._get_max_sequence(images_dir, project_name)
            next_seq = max(next_seq, existing_max + 1)

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
