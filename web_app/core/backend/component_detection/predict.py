"""
Component Detection using YOLO
Provides electrical component detection for SLD diagrams.
"""

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️ OpenCV not available - using PIL for image processing")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("⚠️ NumPy not available - using basic Python operations")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ PIL not available - limited image processing")

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
import json
import time

from .config import model_config

logger = logging.getLogger(__name__)

@dataclass
class Detection:
    """Single detection result"""
    class_name: str
    confidence: float
    bbox: Dict[str, float]  # {x1, y1, x2, y2}
    center: Dict[str, float]  # {x, y}
    area: float

@dataclass
class DetectionResult:
    """Complete detection result for an image"""
    image_path: str
    detections: List[Detection]
    image_dimensions: Dict[str, int]  # {width, height}
    processing_time: float
    model_info: Dict[str, Any]

class ComponentDetector:
    """
    YOLO-based component detector for electrical SLD diagrams.
    Detects Circuit Breakers, HRC Fuses, Isolators, and other electrical components.
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        model_path: Optional[str] = None,
        confidence_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
        device: str = "auto"
    ):
        """
        Initialize the component detector.

        Args:
            model_name: Name of model configuration to use
            model_path: Path to YOLO model weights (overrides model_name)
            confidence_threshold: Minimum confidence for detections
            iou_threshold: IoU threshold for NMS
            device: Device for inference (auto, cpu, cuda)
        """
        # Load model configuration
        if model_path is not None:
            # Use custom model path
            self.model_path = str(model_path)
            self.confidence_threshold = confidence_threshold or 0.03
            self.iou_threshold = iou_threshold or 0.45
            self.class_names = model_config.get_class_names("electrical_components")
        else:
            # Use configured model
            config = model_config.get_model_config(model_name)
            self.model_path = config["model_path"]
            self.confidence_threshold = confidence_threshold or config["confidence_threshold"]
            self.iou_threshold = iou_threshold or config["iou_threshold"]
            self.class_names = config["classes"]

        self.device = device
        self.model = None
        self._load_model()
    
    def _get_class_specific_threshold(self, class_name: str) -> float:
        """
        Get class-specific confidence threshold to improve detection accuracy.

        Based on analysis:
        - Cable Termination Box: Higher threshold to reduce false positives
        - Single Phase Tap-Off Unit: Lower threshold to catch more instances
        - Other classes: Use default threshold
        """
        class_thresholds = {
            "Cable Termination Box": 0.08,  # Higher to reduce false positives
            "Single Phase Tap-Off Unit": 0.03,  # Lower to catch more instances
            "Ammeter": 0.05,  # Default
            "voltmeter": 0.05,  # Default
            "Earth Electrode": 0.05,  # Default
        }

        return class_thresholds.get(class_name, self.confidence_threshold)

    def _load_model(self):
        """Load the YOLO model with compatibility handling"""
        try:
            # Try to import ultralytics YOLO
            try:
                from ultralytics import YOLO

                # Check if trained model file exists
                if Path(self.model_path).exists():
                    try:
                        # Try to load the trained model
                        logger.info(f"🔄 Attempting to load trained model from {self.model_path}")
                        self.model = YOLO(self.model_path)
                        logger.info(f"✅ Loaded trained electrical components YOLO model from {self.model_path}")

                        # STRICT VALIDATION: Ensure it's the 5-class model
                        if hasattr(self.model, 'model') and hasattr(self.model.model, 'names'):
                            class_count = len(self.model.model.names)
                            class_names = self.model.model.names

                            if class_count != 5:
                                logger.error(f"❌ WRONG MODEL: Expected 5 classes, got {class_count}")
                                logger.error(f"❌ Model classes: {class_names}")
                                logger.error("❌ This is not the custom trained 5-class model!")
                                self.model = None
                                return

                            # Verify class names match training data
                            expected_classes = {
                                0: "Ammeter",
                                1: "Cable Termination Box",
                                2: "Earth Electrode",
                                3: "Single Phase Tap-Off Unit",
                                4: "voltmeter"
                            }

                            for class_id, expected_name in expected_classes.items():
                                if class_id not in class_names or class_names[class_id] != expected_name:
                                    logger.error(f"❌ CLASS MISMATCH: Expected '{expected_name}' at ID {class_id}, got '{class_names.get(class_id, 'MISSING')}'")
                                    self.model = None
                                    return

                            logger.info(f"✅ VERIFIED: Correct 5-class model with proper class names")
                            logger.info(f"📋 Classes: {class_names}")

                        # Test the model with a simple prediction to ensure it works
                        try:
                            # Create a small test image to verify model works
                            import numpy as np
                            test_img = np.zeros((640, 640, 3), dtype=np.uint8)
                            results = self.model(test_img, verbose=False)
                            logger.info(f"✅ Model validation successful - ready for inference")
                            return
                        except Exception as test_e:
                            logger.warning(f"⚠️ Model loaded but validation failed: {test_e}")
                            # Model loaded but might have issues, continue anyway
                            return

                    except Exception as model_e:
                        logger.error(f"❌ Failed to load trained model: {model_e}")
                        # Model file may be corrupted, provide guidance
                        logger.error(f"❌ Failed to load custom model: {model_e}")
                        logger.error("⚠️  Model file may be corrupted. Using mock detections as fallback.")
                        logger.error("📋 Please retrain the model using: python electrical_training/scripts/train_model.py")
                        return
                        self.model = None
                        return
                else:
                    logger.error(f"❌ Trained model not found at {self.model_path}")

                # NO FALLBACK - Only use the custom trained model
                logger.error("❌ Custom trained model failed to load - NO FALLBACK ALLOWED")
                logger.error("❌ Only the 5-class custom model should be used")
                self.model = None

            except ImportError as e:
                logger.error(f"❌ Ultralytics not available: {e}")
                logger.error("❌ Install ultralytics: pip install ultralytics")
                self.model = None

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None
    
    def _create_mock_detections(self, image_path: str, image_shape: Tuple[int, int]) -> List[Detection]:
        """Disabled - only use real trained model for the 5 classes"""
        height, width = image_shape

        # Mock detections disabled - only use real trained model
        logger.warning("⚠️ Mock detections disabled - please ensure your trained model is working")
        return []  # Return empty list instead of mock detections
    
    def predict(
        self,
        image_path: Union[str, Path],
        save_visualization: bool = False,
        output_dir: Optional[str] = None
    ) -> DetectionResult:
        """
        Predict electrical components in an SLD image.
        
        Args:
            image_path: Path to input image
            save_visualization: Whether to save visualization
            output_dir: Directory for outputs
            
        Returns:
            DetectionResult object
        """
        start_time = time.time()
        image_path = str(image_path)
        
        # Load and validate image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        height, width = image.shape[:2]
        image_dimensions = {"width": width, "height": height}
        
        detections = []

        if self.model is not None:
            try:
                logger.info(f"🔍 Running YOLO inference on {image_path}")
                # Run YOLO inference with optimized parameters for small components
                results = self.model(
                    image_path,
                    conf=self.confidence_threshold,
                    iou=self.iou_threshold,
                    imgsz=1280,  # Larger image size for better small object detection
                    augment=True,  # Enable test-time augmentation
                    agnostic_nms=False,  # Class-specific NMS for better precision
                    max_det=300,  # Allow more detections for small components
                    verbose=False
                )

                # Process results
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        logger.info(f"📊 Found {len(boxes)} detections")
                        for box in boxes:
                            # Extract box data
                            xyxy = box.xyxy[0].cpu().numpy()
                            conf = float(box.conf[0].cpu().numpy())
                            cls = int(box.cls[0].cpu().numpy())

                            # Get class name
                            class_name = self.class_names.get(cls, f"CLASS_{cls}")

                            # Apply class-specific confidence threshold for better accuracy
                            class_threshold = self._get_class_specific_threshold(class_name)
                            if conf < class_threshold:
                                logger.debug(f"🔍 Filtered {class_name} (conf: {conf:.3f} < threshold: {class_threshold:.3f})")
                                continue

                            # Calculate center and area
                            x1, y1, x2, y2 = xyxy
                            center_x = (x1 + x2) / 2
                            center_y = (y1 + y2) / 2
                            area = (x2 - x1) * (y2 - y1)

                            detection = Detection(
                                class_name=class_name,
                                confidence=conf,
                                bbox={"x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2)},
                                center={"x": float(center_x), "y": float(center_y)},
                                area=float(area)
                            )
                            detections.append(detection)
                            logger.info(f"✅ Detected {class_name} with confidence {conf:.3f}")
                    else:
                        logger.warning("⚠️ No detections found in image")

            except Exception as e:
                logger.error(f"❌ YOLO inference failed: {e}")
                logger.warning("⚠️ Falling back to mock detections")
                detections = self._create_mock_detections(image_path, (height, width))
        else:
            # Use mock detections when model is not available
            logger.warning("⚠️ No YOLO model available, using mock detections")
            detections = self._create_mock_detections(image_path, (height, width))
        
        processing_time = time.time() - start_time
        
        # Create result
        result = DetectionResult(
            image_path=image_path,
            detections=detections,
            image_dimensions=image_dimensions,
            processing_time=processing_time,
            model_info={
                "model_path": self.model_path,
                "confidence_threshold": self.confidence_threshold,
                "iou_threshold": self.iou_threshold,
                "device": self.device,
                "total_detections": len(detections)
            }
        )
        
        # Save visualization if requested
        if save_visualization and output_dir:
            self._save_visualization(image, result, output_dir)
        
        logger.info(f"Detected {len(detections)} components in {processing_time:.2f}s")
        return result
    
    def _save_visualization(self, image: np.ndarray, result: DetectionResult, output_dir: str):
        """Save visualization with bounding boxes"""
        try:
            output_path = Path(output_dir) / f"detection_{Path(result.image_path).stem}.jpg"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Draw bounding boxes
            vis_image = image.copy()
            for detection in result.detections:
                bbox = detection.bbox
                x1, y1, x2, y2 = int(bbox["x1"]), int(bbox["y1"]), int(bbox["x2"]), int(bbox["y2"])
                
                # Draw rectangle
                cv2.rectangle(vis_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Draw label
                label = f"{detection.class_name}: {detection.confidence:.2f}"
                cv2.putText(vis_image, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            cv2.imwrite(str(output_path), vis_image)
            logger.info(f"Visualization saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save visualization: {e}")
    
    def predict_batch(
        self,
        image_paths: List[Union[str, Path]],
        save_visualizations: bool = False,
        output_dir: Optional[str] = None
    ) -> List[DetectionResult]:
        """Predict components in multiple images"""
        results = []
        for image_path in image_paths:
            try:
                result = self.predict(image_path, save_visualizations, output_dir)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {image_path}: {e}")
        
        return results
    
    def export_results(
        self,
        result: DetectionResult,
        output_path: Union[str, Path],
        format: str = "json"
    ):
        """Export detection results to file"""
        output_path = Path(output_path)
        
        if format.lower() == "json":
            # Convert to JSON-serializable format
            data = {
                "image_path": result.image_path,
                "image_dimensions": result.image_dimensions,
                "processing_time": result.processing_time,
                "model_info": result.model_info,
                "detections": [
                    {
                        "class_name": d.class_name,
                        "confidence": d.confidence,
                        "bbox": d.bbox,
                        "center": d.center,
                        "area": d.area
                    }
                    for d in result.detections
                ]
            }
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
        
        logger.info(f"Results exported to {output_path}")
