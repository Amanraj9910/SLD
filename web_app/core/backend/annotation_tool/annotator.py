"""
Annotation Tool Module for SLD Processing
Provides manual labeling interface with canvas-based bounding box drawing.
"""

import os
import json
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass, asdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Annotation:
    """Data class for individual annotations"""
    class_id: int
    class_name: str
    bbox: Tuple[float, float, float, float]  # (x_center, y_center, width, height) normalized
    confidence: float = 1.0
    annotator: str = "manual"
    timestamp: Optional[str] = None

@dataclass
class AnnotationProject:
    """Data class for annotation project"""
    image_path: str
    image_dimensions: Tuple[int, int]  # (width, height)
    annotations: List[Annotation]
    class_names: Dict[int, str]
    project_name: str
    created_by: str
    last_modified: Optional[str] = None

class AnnotationManager:
    """
    Manages annotation projects and provides tools for manual labeling.
    
    Features:
    - Canvas-based bounding box drawing
    - Component category management
    - YOLO format export/import
    - Data validation and error handling
    """
    
    # Default component classes for SLD diagrams
    DEFAULT_CLASSES = {
        0: "CIRCUIT_BREAKER",
        1: "HRC_FUSE",
        2: "ISOLATOR", 
        3: "CABLE_TERMINATION_BOX",
        4: "SINGLE_PHASE_TAP_OFF_UNIT",
        5: "TRANSFORMER",
        6: "MOTOR",
        7: "GENERATOR",
        8: "SWITCH",
        9: "RELAY"
    }
    
    def __init__(
        self,
        class_names: Optional[Dict[int, str]] = None,
        project_dir: Optional[str] = None
    ):
        """
        Initialize the annotation manager.
        
        Args:
            class_names: Dictionary mapping class IDs to names
            project_dir: Directory to store annotation projects
        """
        self.class_names = class_names or self.DEFAULT_CLASSES.copy()
        self.project_dir = Path(project_dir) if project_dir else Path("annotation_projects")
        self.project_dir.mkdir(exist_ok=True)
        
        self.current_project: Optional[AnnotationProject] = None
        
        logger.info(f"Initialized annotation manager with {len(self.class_names)} classes")
    
    def create_project(
        self,
        image_path: Union[str, Path],
        project_name: str,
        created_by: str = "user"
    ) -> AnnotationProject:
        """
        Create a new annotation project.
        
        Args:
            image_path: Path to the image to annotate
            project_name: Name of the project
            created_by: Name of the person creating the project
            
        Returns:
            AnnotationProject object
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Load image to get dimensions
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        height, width = image.shape[:2]
        
        # Create project
        project = AnnotationProject(
            image_path=str(image_path),
            image_dimensions=(width, height),
            annotations=[],
            class_names=self.class_names.copy(),
            project_name=project_name,
            created_by=created_by,
            last_modified=None
        )
        
        self.current_project = project
        logger.info(f"Created project '{project_name}' for image: {image_path}")
        
        return project
    
    def load_project(self, project_path: Union[str, Path]) -> AnnotationProject:
        """
        Load an existing annotation project.
        
        Args:
            project_path: Path to the project JSON file
            
        Returns:
            AnnotationProject object
        """
        project_path = Path(project_path)
        if not project_path.exists():
            raise FileNotFoundError(f"Project file not found: {project_path}")
        
        try:
            with open(project_path, 'r') as f:
                data = json.load(f)
            
            # Convert annotations back to Annotation objects
            annotations = [
                Annotation(**ann_data) for ann_data in data.get('annotations', [])
            ]
            
            project = AnnotationProject(
                image_path=data['image_path'],
                image_dimensions=tuple(data['image_dimensions']),
                annotations=annotations,
                class_names=data.get('class_names', self.DEFAULT_CLASSES),
                project_name=data['project_name'],
                created_by=data['created_by'],
                last_modified=data.get('last_modified')
            )
            
            self.current_project = project
            logger.info(f"Loaded project '{project.project_name}' with {len(annotations)} annotations")
            
            return project
            
        except Exception as e:
            logger.error(f"Failed to load project: {e}")
            raise RuntimeError(f"Could not load project from {project_path}: {e}")
    
    def save_project(
        self,
        project: Optional[AnnotationProject] = None,
        output_path: Optional[Union[str, Path]] = None
    ):
        """
        Save annotation project to file.
        
        Args:
            project: Project to save (uses current project if None)
            output_path: Path to save the project (auto-generated if None)
        """
        project = project or self.current_project
        if not project:
            raise ValueError("No project to save")
        
        if output_path is None:
            output_path = self.project_dir / f"{project.project_name}.json"
        else:
            output_path = Path(output_path)
        
        # Update last modified timestamp
        from datetime import datetime
        project.last_modified = datetime.now().isoformat()
        
        # Convert to dictionary for JSON serialization
        project_data = asdict(project)
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(project_data, f, indent=2)
            
            logger.info(f"Saved project to: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save project: {e}")
            raise RuntimeError(f"Could not save project to {output_path}: {e}")
    
    def add_annotation(
        self,
        class_id: int,
        bbox: Tuple[float, float, float, float],
        confidence: float = 1.0,
        annotator: str = "manual"
    ):
        """
        Add an annotation to the current project.
        
        Args:
            class_id: Class ID of the component
            bbox: Bounding box in YOLO format (x_center, y_center, width, height) normalized
            confidence: Confidence score (default: 1.0 for manual annotations)
            annotator: Name of the annotator
        """
        if not self.current_project:
            raise ValueError("No active project")
        
        if class_id not in self.class_names:
            raise ValueError(f"Invalid class ID: {class_id}")
        
        # Validate bbox format
        if not all(0 <= coord <= 1 for coord in bbox):
            raise ValueError("Bounding box coordinates must be normalized (0-1)")
        
        annotation = Annotation(
            class_id=class_id,
            class_name=self.class_names[class_id],
            bbox=bbox,
            confidence=confidence,
            annotator=annotator,
            timestamp=None
        )
        
        self.current_project.annotations.append(annotation)
        logger.info(f"Added annotation: {annotation.class_name} at {bbox}")
    
    def remove_annotation(self, index: int):
        """Remove an annotation by index"""
        if not self.current_project:
            raise ValueError("No active project")
        
        if 0 <= index < len(self.current_project.annotations):
            removed = self.current_project.annotations.pop(index)
            logger.info(f"Removed annotation: {removed.class_name}")
        else:
            raise IndexError(f"Invalid annotation index: {index}")
    
    def update_annotation(
        self,
        index: int,
        class_id: Optional[int] = None,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        confidence: Optional[float] = None
    ):
        """Update an existing annotation"""
        if not self.current_project:
            raise ValueError("No active project")
        
        if not (0 <= index < len(self.current_project.annotations)):
            raise IndexError(f"Invalid annotation index: {index}")
        
        annotation = self.current_project.annotations[index]
        
        if class_id is not None:
            if class_id not in self.class_names:
                raise ValueError(f"Invalid class ID: {class_id}")
            annotation.class_id = class_id
            annotation.class_name = self.class_names[class_id]
        
        if bbox is not None:
            if not all(0 <= coord <= 1 for coord in bbox):
                raise ValueError("Bounding box coordinates must be normalized (0-1)")
            annotation.bbox = bbox
        
        if confidence is not None:
            annotation.confidence = confidence
        
        logger.info(f"Updated annotation {index}: {annotation.class_name}")
    
    def export_yolo_format(
        self,
        output_dir: Union[str, Path],
        project: Optional[AnnotationProject] = None
    ):
        """
        Export annotations in YOLO format.
        
        Args:
            output_dir: Directory to save YOLO files
            project: Project to export (uses current project if None)
        """
        project = project or self.current_project
        if not project:
            raise ValueError("No project to export")
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get image filename without extension
        image_path = Path(project.image_path)
        base_name = image_path.stem
        
        # Export annotations file
        annotations_file = output_dir / f"{base_name}.txt"
        with open(annotations_file, 'w') as f:
            for ann in project.annotations:
                x_center, y_center, width, height = ann.bbox
                f.write(f"{ann.class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
        
        # Export class names file
        classes_file = output_dir / "classes.txt"
        with open(classes_file, 'w') as f:
            for class_id in sorted(project.class_names.keys()):
                f.write(f"{project.class_names[class_id]}\n")
        
        # Copy image file
        import shutil
        image_dest = output_dir / image_path.name
        if not image_dest.exists():
            shutil.copy2(project.image_path, image_dest)
        
        logger.info(f"Exported YOLO format to: {output_dir}")
        logger.info(f"Files created: {annotations_file.name}, {classes_file.name}, {image_dest.name}")
    
    def import_yolo_format(
        self,
        annotations_file: Union[str, Path],
        image_path: Union[str, Path],
        classes_file: Optional[Union[str, Path]] = None,
        project_name: Optional[str] = None
    ) -> AnnotationProject:
        """
        Import annotations from YOLO format.
        
        Args:
            annotations_file: Path to YOLO annotations file (.txt)
            image_path: Path to the corresponding image
            classes_file: Path to classes file (optional)
            project_name: Name for the new project
            
        Returns:
            AnnotationProject object
        """
        annotations_file = Path(annotations_file)
        image_path = Path(image_path)
        
        if not annotations_file.exists():
            raise FileNotFoundError(f"Annotations file not found: {annotations_file}")
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Load class names if provided
        class_names = self.class_names.copy()
        if classes_file:
            classes_file = Path(classes_file)
            if classes_file.exists():
                with open(classes_file, 'r') as f:
                    lines = f.read().strip().split('\n')
                    class_names = {i: name.strip() for i, name in enumerate(lines) if name.strip()}
        
        # Create project
        project_name = project_name or f"imported_{image_path.stem}"
        project = self.create_project(image_path, project_name)
        project.class_names = class_names
        
        # Load annotations
        with open(annotations_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    parts = line.split()
                    if len(parts) != 5:
                        logger.warning(f"Invalid annotation format at line {line_num}: {line}")
                        continue
                    
                    class_id = int(parts[0])
                    x_center = float(parts[1])
                    y_center = float(parts[2])
                    width = float(parts[3])
                    height = float(parts[4])
                    
                    bbox = (x_center, y_center, width, height)
                    
                    # Validate coordinates
                    if not all(0 <= coord <= 1 for coord in bbox):
                        logger.warning(f"Invalid coordinates at line {line_num}: {bbox}")
                        continue
                    
                    self.add_annotation(
                        class_id=class_id,
                        bbox=bbox,
                        confidence=1.0,
                        annotator="imported"
                    )
                    
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing line {line_num}: {e}")
                    continue
        
        logger.info(f"Imported {len(project.annotations)} annotations from YOLO format")
        return project
    
    def validate_annotations(
        self,
        project: Optional[AnnotationProject] = None
    ) -> Dict[str, List[str]]:
        """
        Validate annotations and return any issues found.
        
        Args:
            project: Project to validate (uses current project if None)
            
        Returns:
            Dictionary with validation results
        """
        project = project or self.current_project
        if not project:
            raise ValueError("No project to validate")
        
        issues = {
            "errors": [],
            "warnings": [],
            "info": []
        }
        
        # Check if image exists
        if not Path(project.image_path).exists():
            issues["errors"].append(f"Image file not found: {project.image_path}")
        
        # Validate annotations
        for i, ann in enumerate(project.annotations):
            # Check class ID
            if ann.class_id not in project.class_names:
                issues["errors"].append(f"Annotation {i}: Invalid class ID {ann.class_id}")
            
            # Check bbox coordinates
            x_center, y_center, width, height = ann.bbox
            if not (0 <= x_center <= 1 and 0 <= y_center <= 1):
                issues["errors"].append(f"Annotation {i}: Center coordinates out of range")
            
            if not (0 < width <= 1 and 0 < height <= 1):
                issues["errors"].append(f"Annotation {i}: Invalid dimensions")
            
            # Check for very small boxes
            if width < 0.01 or height < 0.01:
                issues["warnings"].append(f"Annotation {i}: Very small bounding box")
            
            # Check confidence
            if not (0 <= ann.confidence <= 1):
                issues["warnings"].append(f"Annotation {i}: Confidence out of range")
        
        # Summary
        issues["info"].append(f"Total annotations: {len(project.annotations)}")
        issues["info"].append(f"Classes used: {len(set(ann.class_id for ann in project.annotations))}")
        
        return issues
    
    def get_annotation_statistics(
        self,
        project: Optional[AnnotationProject] = None
    ) -> Dict[str, any]:
        """Get statistics about annotations in the project"""
        project = project or self.current_project
        if not project:
            raise ValueError("No project available")
        
        if not project.annotations:
            return {"total": 0, "by_class": {}, "avg_confidence": 0}
        
        # Count by class
        class_counts = {}
        total_confidence = 0
        
        for ann in project.annotations:
            class_name = ann.class_name
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
            total_confidence += ann.confidence
        
        return {
            "total": len(project.annotations),
            "by_class": class_counts,
            "avg_confidence": total_confidence / len(project.annotations),
            "classes_used": len(class_counts),
            "image_dimensions": project.image_dimensions
        }

# Utility functions for coordinate conversion
def yolo_to_pixel(
    bbox: Tuple[float, float, float, float],
    image_width: int,
    image_height: int
) -> Tuple[int, int, int, int]:
    """Convert YOLO format to pixel coordinates"""
    x_center, y_center, width, height = bbox
    
    # Convert to pixel coordinates
    x_center_px = x_center * image_width
    y_center_px = y_center * image_height
    width_px = width * image_width
    height_px = height * image_height
    
    # Convert to corner coordinates
    x1 = int(x_center_px - width_px / 2)
    y1 = int(y_center_px - height_px / 2)
    x2 = int(x_center_px + width_px / 2)
    y2 = int(y_center_px + height_px / 2)
    
    return (x1, y1, x2, y2)

def pixel_to_yolo(
    bbox: Tuple[int, int, int, int],
    image_width: int,
    image_height: int
) -> Tuple[float, float, float, float]:
    """Convert pixel coordinates to YOLO format"""
    x1, y1, x2, y2 = bbox
    
    # Calculate center and dimensions
    x_center = (x1 + x2) / 2 / image_width
    y_center = (y1 + y2) / 2 / image_height
    width = (x2 - x1) / image_width
    height = (y2 - y1) / image_height
    
    return (x_center, y_center, width, height)

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python annotator.py <command> [args...]")
        print("Commands:")
        print("  create <image_path> <project_name>")
        print("  load <project_path>")
        print("  export <output_dir>")
        print("  import <annotations_file> <image_path> [classes_file]")
        print("  validate [project_path]")
        sys.exit(1)
    
    command = sys.argv[1]
    manager = AnnotationManager()
    
    if command == "create":
        if len(sys.argv) < 4:
            print("Usage: python annotator.py create <image_path> <project_name>")
            sys.exit(1)
        
        image_path = sys.argv[2]
        project_name = sys.argv[3]
        
        project = manager.create_project(image_path, project_name)
        manager.save_project()
        print(f"Created project '{project_name}' for image: {image_path}")
    
    elif command == "load":
        if len(sys.argv) < 3:
            print("Usage: python annotator.py load <project_path>")
            sys.exit(1)
        
        project_path = sys.argv[2]
        project = manager.load_project(project_path)
        print(f"Loaded project '{project.project_name}' with {len(project.annotations)} annotations")
    
    elif command == "export":
        if len(sys.argv) < 3:
            print("Usage: python annotator.py export <output_dir>")
            sys.exit(1)
        
        output_dir = sys.argv[2]
        manager.export_yolo_format(output_dir)
        print(f"Exported annotations to: {output_dir}")
    
    elif command == "import":
        if len(sys.argv) < 4:
            print("Usage: python annotator.py import <annotations_file> <image_path> [classes_file]")
            sys.exit(1)
        
        annotations_file = sys.argv[2]
        image_path = sys.argv[3]
        classes_file = sys.argv[4] if len(sys.argv) > 4 else None
        
        project = manager.import_yolo_format(annotations_file, image_path, classes_file)
        manager.save_project()
        print(f"Imported project with {len(project.annotations)} annotations")
    
    elif command == "validate":
        if len(sys.argv) > 2:
            project_path = sys.argv[2]
            manager.load_project(project_path)
        
        issues = manager.validate_annotations()
        
        print("Validation Results:")
        if issues["errors"]:
            print("Errors:")
            for error in issues["errors"]:
                print(f"  - {error}")
        
        if issues["warnings"]:
            print("Warnings:")
            for warning in issues["warnings"]:
                print(f"  - {warning}")
        
        print("Info:")
        for info in issues["info"]:
            print(f"  - {info}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
