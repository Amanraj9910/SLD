"""
Annotation Tool Module for SLD Processing

This module provides manual labeling interface with canvas-based bounding box drawing,
component category management, and YOLO format export capabilities.

Main Components:
- AnnotationManager: Main class for managing annotation projects
- Annotation: Data class for individual annotations
- AnnotationProject: Data class for complete projects
- Utility functions for coordinate conversion

Example Usage:
    from annotation_tool import AnnotationManager
    
    manager = AnnotationManager()
    project = manager.create_project("sld_diagram.jpg", "my_project")
    manager.add_annotation(class_id=0, bbox=(0.5, 0.3, 0.1, 0.15))
    manager.save_project()
"""

from .annotator import (
    AnnotationManager,
    Annotation,
    AnnotationProject,
    yolo_to_pixel,
    pixel_to_yolo
)

__version__ = "1.0.0"
__author__ = "SLD Processing Team"

__all__ = [
    "AnnotationManager",
    "Annotation",
    "AnnotationProject",
    "yolo_to_pixel",
    "pixel_to_yolo"
]
