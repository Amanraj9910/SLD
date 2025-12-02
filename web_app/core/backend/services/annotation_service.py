"""
Annotation Service
Wraps the annotation tool module for use in the web API.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Union, Tuple, Dict, List
import sys

# Add the parent directories to the path to import our modules
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from annotation_tool.annotator import AnnotationManager, AnnotationProject
from utils.logging_config import log_performance

logger = logging.getLogger(__name__)

class AnnotationService:
    """
    Service wrapper for annotation functionality.
    Provides async interface and additional features for web API.
    """
    
    def __init__(
        self,
        class_names: Optional[Dict[int, str]] = None,
        project_dir: Optional[str] = None
    ):
        """
        Initialize the annotation service.
        
        Args:
            class_names: Dictionary mapping class IDs to names
            project_dir: Directory to store annotation projects
        """
        # Initialize annotation manager
        self._manager = AnnotationManager(
            class_names=class_names,
            project_dir=project_dir or "annotation_projects"
        )
        
        logger.info("Annotation service initialized successfully")
    
    @property
    def current_project(self) -> Optional[AnnotationProject]:
        """Get the current project"""
        return self._manager.current_project
    
    @property
    def class_names(self) -> Dict[int, str]:
        """Get class names mapping"""
        return self._manager.class_names
    
    @property
    def project_dir(self) -> Path:
        """Get project directory"""
        return self._manager.project_dir
    
    @log_performance("Create Annotation Project")
    async def create_project_async(
        self,
        image_path: Union[str, Path],
        project_name: str,
        created_by: str = "user"
    ) -> AnnotationProject:
        """
        Async wrapper for creating annotation project.
        
        Args:
            image_path: Path to the image to annotate
            project_name: Name of the project
            created_by: Name of the person creating the project
            
        Returns:
            AnnotationProject object
        """
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        project = await loop.run_in_executor(
            None,
            self._manager.create_project,
            image_path,
            project_name,
            created_by
        )
        
        return project
    
    def create_project_sync(
        self,
        image_path: Union[str, Path],
        project_name: str,
        created_by: str = "user"
    ) -> AnnotationProject:
        """
        Synchronous project creation.
        
        Args:
            image_path: Path to the image to annotate
            project_name: Name of the project
            created_by: Name of the person creating the project
            
        Returns:
            AnnotationProject object
        """
        return self._manager.create_project(
            image_path=image_path,
            project_name=project_name,
            created_by=created_by
        )
    
    async def load_project_async(
        self,
        project_identifier: Union[str, Path]
    ) -> AnnotationProject:
        """
        Async wrapper for loading annotation project.
        
        Args:
            project_identifier: Project name or path to project file
            
        Returns:
            AnnotationProject object
        """
        # Determine if it's a project name or file path
        if isinstance(project_identifier, str) and not project_identifier.endswith('.json'):
            # It's a project name, construct the path
            project_path = self._manager.project_dir / f"{project_identifier}.json"
        else:
            project_path = project_identifier
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        project = await loop.run_in_executor(
            None,
            self._manager.load_project,
            project_path
        )
        
        return project
    
    def load_project_sync(
        self,
        project_identifier: Union[str, Path]
    ) -> AnnotationProject:
        """
        Synchronous project loading.
        
        Args:
            project_identifier: Project name or path to project file
            
        Returns:
            AnnotationProject object
        """
        # Determine if it's a project name or file path
        if isinstance(project_identifier, str) and not project_identifier.endswith('.json'):
            # It's a project name, construct the path
            project_path = self._manager.project_dir / f"{project_identifier}.json"
        else:
            project_path = project_identifier
        
        return self._manager.load_project(project_path)
    
    async def save_project_async(
        self,
        project: Optional[AnnotationProject] = None,
        output_path: Optional[Union[str, Path]] = None
    ):
        """
        Async wrapper for saving annotation project.
        
        Args:
            project: Project to save (uses current project if None)
            output_path: Path to save the project (auto-generated if None)
        """
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._manager.save_project,
            project,
            output_path
        )
    
    def save_project_sync(
        self,
        project: Optional[AnnotationProject] = None,
        output_path: Optional[Union[str, Path]] = None
    ):
        """
        Synchronous project saving.
        
        Args:
            project: Project to save (uses current project if None)
            output_path: Path to save the project (auto-generated if None)
        """
        self._manager.save_project(project, output_path)
    
    async def add_annotation_async(
        self,
        class_id: int,
        bbox: Tuple[float, float, float, float],
        confidence: float = 1.0,
        annotator: str = "manual"
    ):
        """
        Async wrapper for adding annotation.
        
        Args:
            class_id: Class ID of the component
            bbox: Bounding box in YOLO format (x_center, y_center, width, height) normalized
            confidence: Confidence score
            annotator: Name of the annotator
        """
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._manager.add_annotation,
            class_id,
            bbox,
            confidence,
            annotator
        )
    
    def add_annotation_sync(
        self,
        class_id: int,
        bbox: Tuple[float, float, float, float],
        confidence: float = 1.0,
        annotator: str = "manual"
    ):
        """
        Synchronous annotation addition.
        
        Args:
            class_id: Class ID of the component
            bbox: Bounding box in YOLO format
            confidence: Confidence score
            annotator: Name of the annotator
        """
        self._manager.add_annotation(
            class_id=class_id,
            bbox=bbox,
            confidence=confidence,
            annotator=annotator
        )
    
    async def remove_annotation_async(self, index: int):
        """Async wrapper for removing annotation"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._manager.remove_annotation,
            index
        )
    
    def remove_annotation_sync(self, index: int):
        """Synchronous annotation removal"""
        self._manager.remove_annotation(index)
    
    async def update_annotation_async(
        self,
        index: int,
        class_id: Optional[int] = None,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        confidence: Optional[float] = None
    ):
        """Async wrapper for updating annotation"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._manager.update_annotation,
            index,
            class_id,
            bbox,
            confidence
        )
    
    def update_annotation_sync(
        self,
        index: int,
        class_id: Optional[int] = None,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        confidence: Optional[float] = None
    ):
        """Synchronous annotation update"""
        self._manager.update_annotation(
            index=index,
            class_id=class_id,
            bbox=bbox,
            confidence=confidence
        )
    
    async def export_yolo_format_async(
        self,
        output_dir: Union[str, Path],
        project: Optional[AnnotationProject] = None
    ):
        """
        Async wrapper for YOLO format export.
        
        Args:
            output_dir: Directory to save YOLO files
            project: Project to export (uses current project if None)
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._manager.export_yolo_format,
            output_dir,
            project
        )
    
    def export_yolo_format_sync(
        self,
        output_dir: Union[str, Path],
        project: Optional[AnnotationProject] = None
    ):
        """
        Synchronous YOLO format export.
        
        Args:
            output_dir: Directory to save YOLO files
            project: Project to export (uses current project if None)
        """
        self._manager.export_yolo_format(output_dir, project)
    
    async def import_yolo_format_async(
        self,
        annotations_file: Union[str, Path],
        image_path: Union[str, Path],
        classes_file: Optional[Union[str, Path]] = None,
        project_name: Optional[str] = None
    ) -> AnnotationProject:
        """
        Async wrapper for YOLO format import.
        
        Args:
            annotations_file: Path to YOLO annotations file
            image_path: Path to the corresponding image
            classes_file: Path to classes file (optional)
            project_name: Name for the new project
            
        Returns:
            AnnotationProject object
        """
        loop = asyncio.get_event_loop()
        project = await loop.run_in_executor(
            None,
            self._manager.import_yolo_format,
            annotations_file,
            image_path,
            classes_file,
            project_name
        )
        
        return project
    
    def import_yolo_format_sync(
        self,
        annotations_file: Union[str, Path],
        image_path: Union[str, Path],
        classes_file: Optional[Union[str, Path]] = None,
        project_name: Optional[str] = None
    ) -> AnnotationProject:
        """
        Synchronous YOLO format import.
        
        Args:
            annotations_file: Path to YOLO annotations file
            image_path: Path to the corresponding image
            classes_file: Path to classes file (optional)
            project_name: Name for the new project
            
        Returns:
            AnnotationProject object
        """
        return self._manager.import_yolo_format(
            annotations_file=annotations_file,
            image_path=image_path,
            classes_file=classes_file,
            project_name=project_name
        )
    
    async def validate_annotations_async(
        self,
        project: Optional[AnnotationProject] = None
    ) -> Dict[str, List[str]]:
        """
        Async wrapper for annotation validation.
        
        Args:
            project: Project to validate (uses current project if None)
            
        Returns:
            Dictionary with validation results
        """
        loop = asyncio.get_event_loop()
        issues = await loop.run_in_executor(
            None,
            self._manager.validate_annotations,
            project
        )
        
        return issues
    
    def validate_annotations_sync(
        self,
        project: Optional[AnnotationProject] = None
    ) -> Dict[str, List[str]]:
        """
        Synchronous annotation validation.
        
        Args:
            project: Project to validate (uses current project if None)
            
        Returns:
            Dictionary with validation results
        """
        return self._manager.validate_annotations(project)
    
    async def get_statistics_async(
        self,
        project: Optional[AnnotationProject] = None
    ) -> Dict[str, any]:
        """
        Async wrapper for getting annotation statistics.
        
        Args:
            project: Project to analyze (uses current project if None)
            
        Returns:
            Dictionary with statistics
        """
        loop = asyncio.get_event_loop()
        stats = await loop.run_in_executor(
            None,
            self._manager.get_annotation_statistics,
            project
        )
        
        return stats
    
    def get_statistics_sync(
        self,
        project: Optional[AnnotationProject] = None
    ) -> Dict[str, any]:
        """
        Synchronous statistics retrieval.
        
        Args:
            project: Project to analyze (uses current project if None)
            
        Returns:
            Dictionary with statistics
        """
        return self._manager.get_annotation_statistics(project)
    
    def list_projects(self) -> List[Dict[str, any]]:
        """
        List all available annotation projects.
        
        Returns:
            List of project information dictionaries
        """
        projects = []
        
        if not self._manager.project_dir.exists():
            return projects
        
        for project_file in self._manager.project_dir.glob("*.json"):
            try:
                import json
                with open(project_file, 'r') as f:
                    data = json.load(f)
                
                projects.append({
                    "name": data.get("project_name", project_file.stem),
                    "file_path": str(project_file),
                    "image_path": data.get("image_path", ""),
                    "created_by": data.get("created_by", "unknown"),
                    "last_modified": data.get("last_modified", ""),
                    "annotation_count": len(data.get("annotations", [])),
                    "file_size": project_file.stat().st_size
                })
                
            except Exception as e:
                logger.warning(f"Failed to read project file {project_file}: {e}")
                continue
        
        return projects
    
    def delete_project(self, project_name: str) -> bool:
        """
        Delete an annotation project.
        
        Args:
            project_name: Name of the project to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            project_path = self._manager.project_dir / f"{project_name}.json"
            
            if project_path.exists():
                project_path.unlink()
                logger.info(f"Deleted project: {project_name}")
                return True
            else:
                logger.warning(f"Project not found: {project_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete project {project_name}: {e}")
            return False
    
    def get_project_info(self, project_name: str) -> Optional[Dict[str, any]]:
        """
        Get information about a specific project without loading it.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Project information dictionary or None if not found
        """
        try:
            project_path = self._manager.project_dir / f"{project_name}.json"
            
            if not project_path.exists():
                return None
            
            import json
            with open(project_path, 'r') as f:
                data = json.load(f)
            
            return {
                "name": data.get("project_name", project_name),
                "image_path": data.get("image_path", ""),
                "created_by": data.get("created_by", "unknown"),
                "last_modified": data.get("last_modified", ""),
                "annotation_count": len(data.get("annotations", [])),
                "class_names": data.get("class_names", {}),
                "image_dimensions": data.get("image_dimensions", [0, 0])
            }
            
        except Exception as e:
            logger.error(f"Failed to get project info for {project_name}: {e}")
            return None
    
    def cleanup(self):
        """Cleanup resources"""
        # Clear current project
        self._manager.current_project = None
        logger.info("Annotation service cleaned up")

# Singleton instance for the application
_annotation_service_instance = None

def get_annotation_service_instance(**kwargs) -> AnnotationService:
    """Get singleton instance of annotation service"""
    global _annotation_service_instance
    
    if _annotation_service_instance is None:
        _annotation_service_instance = AnnotationService(**kwargs)
    
    return _annotation_service_instance
