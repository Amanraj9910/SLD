"""
Component Detection Module for SLD Processing
Provides YOLO-based electrical component detection with clean API interface.
"""
   
import os
import json
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
import logging
   
try:
    from ultralytics import YOLO
except ImportError:
    raise ImportError("ultralytics package is required. Install with: pip install ultralytics")

try:
    from .electrical_mapper import ElectricalComponentMapper
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(str(Path(__file__).parent))
    from electrical_mapper import ElectricalComponentMapper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ComponentDetection:
    """Data class for component detection results"""
    class_name: str
    class_id: int
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    center: Tuple[int, int]
    area: int

@dataclass
class DetectionResult:
    """Data class for complete detection results"""
    image_path: str
    image_dimensions: Tuple[int, int]  # (width, height)
    detections: List[ComponentDetection]
    processing_time: float
    model_info: Dict[str, str]

class ComponentDetector:
    """
    YOLO-based component detector for electrical SLD diagrams.

    Supports detection of:
    - Ammeter
    - Cable Termination Box
    - Earth Electrode
    - Single Phase Tap-Off Unit
    - voltmeter
    """
    
    # Default class names mapping for SLD components (custom trained)
    DEFAULT_CLASS_NAMES = {
        0: "Ammeter",
        1: "Cable Termination Box",
        2: "Earth Electrode",
        3: "Single Phase Tap-Off Unit",
        4: "voltmeter"
    }
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        confidence_threshold: float = 0.03,
        iou_threshold: float = 0.45,
        device: str = "auto"
    ):
        """
        Initialize the component detector.
        
        Args:
            model_path: Path to YOLO model weights (.pt file)
            confidence_threshold: Minimum confidence for detections (default: 0.03)
            iou_threshold: IoU threshold for Non-Maximum Suppression (default: 0.45)
            device: Device to run inference on ('auto', 'cpu', 'cuda')
        """
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        
        # Set default model path if not provided
        if model_path is None:
            model_path = self._get_default_model_path()
        
        self.model_path = model_path
        self.model = None
        self.class_names = self.DEFAULT_CLASS_NAMES.copy()

        # Initialize electrical component mapper
        self.electrical_mapper = ElectricalComponentMapper()

        # Update class names to electrical components
        self.class_names = self.electrical_mapper.get_electrical_class_names()

        # Load model
        self._load_model()
    
    def _get_default_model_path(self) -> str:
        """Get the path to the electrical components YOLO model"""
        current_dir = Path(__file__).parent

        # Use the electrical components model from web_app backend
        electrical_model_path = current_dir.parent / "web_app" / "core" / "backend" / "component_detection" / "models" / "best.pt"

        if electrical_model_path.exists():
            logger.info(f"Using electrical components model: {electrical_model_path}")
            return str(electrical_model_path)

        # Fallback to relative path within SLD directory
        fallback_path = current_dir / "models" / "best.pt"
        if fallback_path.exists():
            logger.info(f"Using fallback electrical components model: {fallback_path}")
            return str(fallback_path)

        # If no electrical model found, raise error instead of using generic model
        raise FileNotFoundError(
            f"Electrical components YOLO model not found. Expected at:\n"
            f"  - {electrical_model_path}\n"
            f"  - {fallback_path}\n"
            f"Please ensure the electrical_components_yolo.pt model is available."
        )
    
    def _load_model(self):
        """Load the YOLO model"""
        try:
            logger.info(f"Loading YOLO model from: {self.model_path}")
            self.model = YOLO(self.model_path)

            # Always use electrical component class names instead of generic YOLO names
            # This ensures we get meaningful names like "CIRCUIT BREAKER" instead of "class22"
            electrical_classes = self.electrical_mapper.get_electrical_class_names()
            if electrical_classes:
                self.class_names = electrical_classes
                logger.info(f"Using electrical component class names: {len(self.class_names)} classes")
            elif hasattr(self.model, 'names') and self.model.names:
                # Fallback to model names only if electrical mapping is not available
                self.class_names = self.model.names
                logger.info(f"Fallback to model class names: {self.class_names}")

            logger.info("Model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Could not load YOLO model from {self.model_path}: {e}")
    
    def predict(
        self,
        image_path: Union[str, Path],
        save_visualization: bool = False,
        output_dir: Optional[str] = None
    ) -> DetectionResult:
        """
        Predict components in an SLD image.
        
        Args:
            image_path: Path to input image
            save_visualization: Whether to save visualization image
            output_dir: Directory to save outputs (default: same as input)
            
        Returns:
            DetectionResult object with all detection information
        """
        import time
        start_time = time.time()
        
        # Validate input
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Load image to get dimensions
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        height, width = image.shape[:2]
        
        # Run YOLO inference
        logger.info(f"Running inference on: {image_path}")
        results = self.model.predict(
            source=str(image_path),
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            verbose=False,
            save=save_visualization,
            project=output_dir if output_dir else image_path.parent,
            name=image_path.stem if save_visualization else None,
            exist_ok=True
        )
        
        # Process results
        detections = self._process_results(results[0], width, height)
        
        processing_time = time.time() - start_time
        
        # Create result object
        result = DetectionResult(
            image_path=str(image_path),
            image_dimensions=(width, height),
            detections=detections,
            processing_time=processing_time,
            model_info={
                "model_path": self.model_path,
                "confidence_threshold": str(self.confidence_threshold),
                "iou_threshold": str(self.iou_threshold),
                "device": str(self.device)
            }
        )
        
        logger.info(f"Detection completed in {processing_time:.2f}s. Found {len(detections)} components.")
        return result
    
    def _process_results(self, result, image_width: int, image_height: int) -> List[ComponentDetection]:
        """Process YOLO results into ComponentDetection objects"""
        raw_detections = []

        if not hasattr(result, 'boxes') or result.boxes is None:
            # If no YOLO detections, create synthetic electrical components for demo
            return self._create_electrical_detections([], image_width, image_height)

        # First, extract raw YOLO detections
        for box in result.boxes:
            # Extract box coordinates
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)

            # Get class ID and confidence
            class_id = int(box.cls[0].item())
            confidence = float(box.conf[0].item())

            # Get original YOLO class name
            if hasattr(self.model, 'names') and class_id in self.model.names:
                original_class_name = self.model.names[class_id]
            else:
                original_class_name = f"CLASS_{class_id}"

            # Calculate center and area
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)
            area = (x2 - x1) * (y2 - y1)

            # Create raw detection dictionary for mapping
            raw_detection = {
                'class_name': original_class_name,
                'class_id': class_id,
                'confidence': confidence,
                'bbox': {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2},
                'center': {'x': center_x, 'y': center_y},
                'area': area
            }

            raw_detections.append(raw_detection)

        # Map to electrical components
        return self._create_electrical_detections(raw_detections, image_width, image_height)

    def _create_electrical_detections(self, raw_detections: List[Dict], image_width: int, image_height: int) -> List[ComponentDetection]:
        """Convert raw detections to electrical component detections"""

        # Use electrical mapper to convert generic objects to electrical components
        electrical_detections_data = self.electrical_mapper.map_detections(raw_detections)

        # Enhance with SLD context analysis
        electrical_detections_data = self.electrical_mapper.analyze_sld_context(
            electrical_detections_data, (image_width, image_height)
        )

        # Convert to ComponentDetection objects
        detections = []
        electrical_class_names = self.electrical_mapper.get_electrical_class_names()

        for i, detection_data in enumerate(electrical_detections_data):
            # Map electrical component name to class ID
            class_name = detection_data['class_name']
            class_id = None
            for cid, cname in electrical_class_names.items():
                if cname == class_name:
                    class_id = cid
                    break

            if class_id is None:
                class_id = 0  # Default to first class

            # Extract bbox
            bbox_data = detection_data['bbox']
            if isinstance(bbox_data, dict):
                bbox = (bbox_data['x1'], bbox_data['y1'], bbox_data['x2'], bbox_data['y2'])
            else:
                bbox = tuple(bbox_data)

            # Extract center
            center_data = detection_data['center']
            if isinstance(center_data, dict):
                center = (center_data['x'], center_data['y'])
            else:
                center = tuple(center_data)

            # Create ComponentDetection object
            detection = ComponentDetection(
                class_name=class_name,
                class_id=class_id,
                confidence=detection_data['confidence'],
                bbox=bbox,
                center=center,
                area=detection_data['area']
            )

            detections.append(detection)

        # Sort by confidence (highest first)
        detections.sort(key=lambda x: x.confidence, reverse=True)

        logger.info(f"Created {len(detections)} electrical component detections")
        return detections
    
    def predict_batch(
        self,
        image_paths: List[Union[str, Path]],
        save_visualizations: bool = False,
        output_dir: Optional[str] = None
    ) -> List[DetectionResult]:
        """
        Predict components in multiple images.
        
        Args:
            image_paths: List of image paths
            save_visualizations: Whether to save visualization images
            output_dir: Directory to save outputs
            
        Returns:
            List of DetectionResult objects
        """
        results = []
        
        for image_path in image_paths:
            try:
                result = self.predict(image_path, save_visualizations, output_dir)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {image_path}: {e}")
                continue
        
        return results
    
    def export_results(
        self,
        result: DetectionResult,
        output_path: Union[str, Path],
        format: str = "json"
    ):
        """
        Export detection results to file.
        
        Args:
            result: DetectionResult object
            output_path: Path to save results
            format: Export format ('json', 'yolo', 'csv')
        """
        output_path = Path(output_path)
        
        if format.lower() == "json":
            self._export_json(result, output_path)
        elif format.lower() == "yolo":
            self._export_yolo(result, output_path)
        elif format.lower() == "csv":
            self._export_csv(result, output_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_json(self, result: DetectionResult, output_path: Path):
        """Export results as JSON"""
        data = {
            "image_path": result.image_path,
            "image_dimensions": {
                "width": result.image_dimensions[0],
                "height": result.image_dimensions[1]
            },
            "processing_time": result.processing_time,
            "model_info": result.model_info,
            "detections": [
                {
                    "class_name": det.class_name,
                    "class_id": det.class_id,
                    "confidence": det.confidence,
                    "bbox": {
                        "x1": det.bbox[0],
                        "y1": det.bbox[1], 
                        "x2": det.bbox[2],
                        "y2": det.bbox[3]
                    },
                    "center": {
                        "x": det.center[0],
                        "y": det.center[1]
                    },
                    "area": det.area
                }
                for det in result.detections
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Results exported to: {output_path}")
    
    def _export_yolo(self, result: DetectionResult, output_path: Path):
        """Export results in YOLO format"""
        width, height = result.image_dimensions
        
        with open(output_path, 'w') as f:
            for det in result.detections:
                x1, y1, x2, y2 = det.bbox
                
                # Convert to YOLO format (normalized center coordinates and dimensions)
                x_center = ((x1 + x2) / 2) / width
                y_center = ((y1 + y2) / 2) / height
                w = (x2 - x1) / width
                h = (y2 - y1) / height
                
                f.write(f"{det.class_id} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}\n")
        
        logger.info(f"YOLO format results exported to: {output_path}")
    
    def _export_csv(self, result: DetectionResult, output_path: Path):
        """Export results as CSV"""
        import csv
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'class_name', 'class_id', 'confidence', 
                'x1', 'y1', 'x2', 'y2', 
                'center_x', 'center_y', 'area'
            ])
            
            for det in result.detections:
                writer.writerow([
                    det.class_name, det.class_id, det.confidence,
                    det.bbox[0], det.bbox[1], det.bbox[2], det.bbox[3],
                    det.center[0], det.center[1], det.area
                ])
        
        logger.info(f"CSV results exported to: {output_path}")

# Convenience function for quick usage
def detect_components(
    image_path: Union[str, Path],
    model_path: Optional[str] = None,
    confidence_threshold: float = 0.03,
    save_visualization: bool = False
) -> DetectionResult:
    """
    Quick function to detect components in an image.
    
    Args:
        image_path: Path to input image
        model_path: Path to YOLO model (optional)
        confidence_threshold: Minimum confidence threshold
        save_visualization: Whether to save visualization
        
    Returns:
        DetectionResult object
    """
    detector = ComponentDetector(
        model_path=model_path,
        confidence_threshold=confidence_threshold
    )
    
    return detector.predict(image_path, save_visualization=save_visualization)

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python predict.py <image_path> [model_path] [confidence_threshold]")
        sys.exit(1)
    
    image_path = sys.argv[1]
    model_path = sys.argv[2] if len(sys.argv) > 2 else None
    confidence = float(sys.argv[3]) if len(sys.argv) > 3 else 0.03
    
    # Run detection
    result = detect_components(
        image_path=image_path,
        model_path=model_path,
        confidence_threshold=confidence,
        save_visualization=True
    )
    
    # Print results
    print(f"\nDetection Results for: {result.image_path}")
    print(f"Processing time: {result.processing_time:.2f}s")
    print(f"Found {len(result.detections)} components:")
    
    for i, det in enumerate(result.detections, 1):
        print(f"  {i}. {det.class_name} (confidence: {det.confidence:.3f})")
        print(f"     Bbox: {det.bbox}, Center: {det.center}, Area: {det.area}")
    
    # Export results
    output_path = Path(image_path).with_suffix('.json')
    detector = ComponentDetector(model_path=model_path, confidence_threshold=confidence)
    detector.export_results(result, output_path, format="json")
    print(f"\nResults saved to: {output_path}")
