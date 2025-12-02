"""
Component Detection Module for SLD Processing

This module provides YOLO-based electrical component detection for Single Line Diagrams.
It includes classes and functions for detecting, processing, and exporting component
detection results.

Main Components:
- ComponentDetector: Main detection class
- ComponentDetection: Data class for individual detections
- DetectionResult: Data class for complete results
- detect_components: Convenience function for quick detection

Example Usage:
    from component_detection import detect_components
    
    result = detect_components("sld_diagram.jpg")
    print(f"Found {len(result.detections)} components")
"""

from .predict import (
    ComponentDetector,
    ComponentDetection,
    DetectionResult,
    detect_components
)

__version__ = "1.0.0"
__author__ = "SLD Processing Team"

__all__ = [
    "ComponentDetector",
    "ComponentDetection", 
    "DetectionResult",
    "detect_components"
]
