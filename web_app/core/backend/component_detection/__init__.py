"""
Component Detection Module
Provides YOLO-based electrical component detection for SLD diagrams.
"""

from .predict import ComponentDetector, Detection, DetectionResult

__all__ = ['ComponentDetector', 'Detection', 'DetectionResult']
