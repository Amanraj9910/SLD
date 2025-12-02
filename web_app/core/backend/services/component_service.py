"""
Component Detection Service
Wraps the component detection module for use in the web API.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Union
import sys

# Add the parent directories to the path to import our modules
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from component_detection.predict import ComponentDetector, DetectionResult
from utils.logging_config import log_performance

logger = logging.getLogger(__name__)

class ComponentDetectionService:
    """
    Service wrapper for component detection functionality.
    Provides async interface and additional features for web API.
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        confidence_threshold: float = 0.03,
        iou_threshold: float = 0.45,
        device: str = "auto"
    ):
        """
        Initialize the component detection service.

        Args:
            model_path: Path to YOLO model weights
            confidence_threshold: Minimum confidence for detections
            iou_threshold: IoU threshold for NMS
            device: Device for inference (auto, cpu, cuda)
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.device = device

        # Initialize detector
        self._detector = None
        self._initialize_detector()
    
    def _initialize_detector(self):
        """Initialize the YOLO detector"""
        try:
            self._detector = ComponentDetector(
                model_path=self.model_path,
                confidence_threshold=self.confidence_threshold,
                iou_threshold=self.iou_threshold,
                device=self.device
            )
            logger.info("Component detector initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize component detector: {e}")
            raise
    
    @property
    def model(self):
        """Get the underlying YOLO model"""
        return self._detector.model if self._detector else None
    
    @property
    def class_names(self):
        """Get class names mapping"""
        return self._detector.class_names if self._detector else {}








    
    @log_performance("Component Detection")
    async def detect_components_async(
        self,
        image_path: Union[str, Path],
        save_visualization: bool = False,
        output_dir: Optional[str] = None
    ) -> DetectionResult:
        """
        Async wrapper for component detection.

        Args:
            image_path: Path to input image
            save_visualization: Whether to save visualization
            output_dir: Directory for outputs

        Returns:
            DetectionResult object
        """
        if not self._detector:
            raise RuntimeError("Component detector not initialized")

        # Update detector parameters
        self._detector.confidence_threshold = self.confidence_threshold
        self._detector.iou_threshold = self.iou_threshold

        # Run detection in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._detector.predict,
            image_path,
            save_visualization,
            output_dir
        )

        return result


    def detect_components_sync(
        self,
        image_path: Union[str, Path],
        save_visualization: bool = False,
        output_dir: Optional[str] = None
    ) -> DetectionResult:
        """
        Synchronous component detection.

        Args:
            image_path: Path to input image
            save_visualization: Whether to save visualization
            output_dir: Directory for outputs

        Returns:
            DetectionResult object
        """
        if not self._detector:
            raise RuntimeError("Component detector not initialized")

        # Update detector parameters
        self._detector.confidence_threshold = self.confidence_threshold
        self._detector.iou_threshold = self.iou_threshold

        return self._detector.predict(
            image_path=image_path,
            save_visualization=save_visualization,
            output_dir=output_dir
        )
    
    async def detect_batch_async(
        self,
        image_paths: list,
        save_visualizations: bool = False,
        output_dir: Optional[str] = None
    ) -> list:
        """
        Async batch component detection.
        
        Args:
            image_paths: List of image paths
            save_visualizations: Whether to save visualizations
            output_dir: Directory for outputs
            
        Returns:
            List of DetectionResult objects
        """
        if not self._detector:
            raise RuntimeError("Component detector not initialized")
        
        # Update detector parameters
        self._detector.confidence_threshold = self.confidence_threshold
        self._detector.iou_threshold = self.iou_threshold
        
        # Run batch detection in thread pool
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            self._detector.predict_batch,
            image_paths,
            save_visualizations,
            output_dir
        )
        
        return results
    
    def export_results(
        self,
        result: DetectionResult,
        output_path: Union[str, Path],
        format: str = "json"
    ):
        """
        Export detection results.
        
        Args:
            result: DetectionResult object
            output_path: Path to save results
            format: Export format (json, yolo, csv)
        """
        if not self._detector:
            raise RuntimeError("Component detector not initialized")
        
        self._detector.export_results(result, output_path, format)
    
    def update_model(self, model_path: str):
        """
        Update the YOLO model.
        
        Args:
            model_path: Path to new model weights
        """
        self.model_path = model_path
        self._initialize_detector()
        logger.info(f"Model updated to: {model_path}")
    
    def update_parameters(
        self,
        confidence_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
        device: Optional[str] = None
    ):
        """
        Update detection parameters.
        
        Args:
            confidence_threshold: New confidence threshold
            iou_threshold: New IoU threshold
            device: New device setting
        """
        if confidence_threshold is not None:
            self.confidence_threshold = confidence_threshold
        
        if iou_threshold is not None:
            self.iou_threshold = iou_threshold
        
        if device is not None:
            self.device = device
            # Reinitialize detector with new device
            self._initialize_detector()
        
        logger.info(f"Parameters updated: conf={self.confidence_threshold}, iou={self.iou_threshold}, device={self.device}")
    
    def get_model_info(self) -> dict:
        """Get information about the current model"""
        if not self._detector:
            return {"error": "Detector not initialized"}
        
        return {
            "model_path": self.model_path,
            "confidence_threshold": self.confidence_threshold,
            "iou_threshold": self.iou_threshold,
            "device": self.device,
            "class_names": self.class_names,
            "total_classes": len(self.class_names)
        }
    
    def validate_image(self, image_path: Union[str, Path]) -> bool:
        """
        Validate if image can be processed.
        
        Args:
            image_path: Path to image file
            
        Returns:
            True if image is valid
        """
        try:
            import cv2
            image = cv2.imread(str(image_path))
            return image is not None
        except Exception:
            return False
    
    def get_supported_formats(self) -> list:
        """Get list of supported image formats"""
        return ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
    
    def cleanup(self):
        """Cleanup resources"""
        if self._detector:
            # Clear model from memory if needed
            self._detector = None
        logger.info("Component detection service cleaned up")

# Singleton instance for the application
_component_service_instance = None

def get_component_service_instance(**kwargs) -> ComponentDetectionService:
    """Get singleton instance of component detection service"""
    global _component_service_instance
    
    if _component_service_instance is None:
        _component_service_instance = ComponentDetectionService(**kwargs)
    
    return _component_service_instance
