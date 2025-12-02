"""
Configuration for Component Detection Models
Manages model paths, thresholds, and detection settings.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ModelConfig:
    """Configuration class for YOLO component detection models"""
    
    def __init__(self):
        # Base paths
        self.base_dir = Path(__file__).parent
        self.models_dir = self.base_dir / "models"
        
        # Ensure models directory exists
        self.models_dir.mkdir(exist_ok=True)
        
        # Model configurations - SLD electrical components detection
        self.model_configs = {
            "electrical_components": {
                "name": "SLD Electrical Components YOLO Model",
                "description": "Specialized YOLO model trained for detecting electrical components in SLD diagrams",
                "model_file": "best.pt",
                "confidence_threshold": 0.01,  # 1% threshold optimized for smaller components
                "iou_threshold": 0.3,  # Lower IoU for better small component detection
                "classes": {
                    # Custom trained classes (5 classes)
                    0: "Ammeter",
                    1: "Cable Termination Box",
                    2: "Earth Electrode",
                    3: "Single Phase Tap-Off Unit",
                    4: "voltmeter"
                }
            }
        }
        
        # Default model to use
        self.default_model = "electrical_components"
        
        # Environment variable overrides
        self._load_env_overrides()
    
    def _load_env_overrides(self):
        """Load configuration overrides from environment variables"""
        
        # Model path override
        env_model_path = os.getenv("SLD_MODEL_PATH")
        if env_model_path:
            model_path = Path(env_model_path)
            if model_path.exists():
                self.model_configs["electrical_components"]["model_file"] = str(model_path)
                logger.info(f"Using model path from environment: {model_path}")
        
        # Confidence threshold override
        env_confidence = os.getenv("SLD_CONFIDENCE_THRESHOLD")
        if env_confidence:
            try:
                confidence = float(env_confidence)
                if 0.0 <= confidence <= 1.0:
                    self.model_configs["electrical_components"]["confidence_threshold"] = confidence
                    logger.info(f"Using confidence threshold from environment: {confidence}")
            except ValueError:
                logger.warning(f"Invalid confidence threshold in environment: {env_confidence}")
        
        # IoU threshold override
        env_iou = os.getenv("SLD_IOU_THRESHOLD")
        if env_iou:
            try:
                iou = float(env_iou)
                if 0.0 <= iou <= 1.0:
                    self.model_configs["electrical_components"]["iou_threshold"] = iou
                    logger.info(f"Using IoU threshold from environment: {iou}")
            except ValueError:
                logger.warning(f"Invalid IoU threshold in environment: {env_iou}")
    
    def get_model_path(self, model_name: str = None) -> str:
        """Get the full path to a model file"""
        if model_name is None:
            model_name = self.default_model
        
        if model_name not in self.model_configs:
            raise ValueError(f"Unknown model: {model_name}")
        
        model_file = self.model_configs[model_name]["model_file"]
        
        # If it's already an absolute path, return as is
        if Path(model_file).is_absolute():
            return model_file
        
        # Otherwise, construct path relative to models directory
        return str(self.models_dir / model_file)
    
    def get_model_config(self, model_name: str = None) -> Dict[str, Any]:
        """Get complete configuration for a model"""
        if model_name is None:
            model_name = self.default_model
        
        if model_name not in self.model_configs:
            raise ValueError(f"Unknown model: {model_name}")
        
        config = self.model_configs[model_name].copy()
        config["model_path"] = self.get_model_path(model_name)
        return config
    
    def list_available_models(self) -> Dict[str, Dict[str, Any]]:
        """List all available model configurations"""
        return {
            name: {
                "name": config["name"],
                "description": config["description"],
                "model_path": self.get_model_path(name),
                "exists": Path(self.get_model_path(name)).exists(),
                "confidence_threshold": config["confidence_threshold"],
                "iou_threshold": config["iou_threshold"],
                "num_classes": len(config["classes"])
            }
            for name, config in self.model_configs.items()
        }
    
    def validate_model_file(self, model_name: str = None) -> bool:
        """Check if model file exists and is accessible"""
        model_path = Path(self.get_model_path(model_name))
        return model_path.exists() and model_path.is_file()
    
    def get_class_names(self, model_name: str = None) -> Dict[int, str]:
        """Get class names for a model"""
        if model_name is None:
            model_name = self.default_model
        
        if model_name not in self.model_configs:
            raise ValueError(f"Unknown model: {model_name}")
        
        return self.model_configs[model_name]["classes"]
    
    def create_model_info_file(self, model_name: str = None):
        """Create a README file with model information"""
        if model_name is None:
            model_name = self.default_model
        
        config = self.get_model_config(model_name)
        
        readme_content = f"""# {config['name']}

## Description
{config['description']}

## Model Configuration
- **Model File**: {config['model_file']}
- **Confidence Threshold**: {config['confidence_threshold']}
- **IoU Threshold**: {config['iou_threshold']}
- **Number of Classes**: {len(config['classes'])}

## Supported Classes
"""
        
        for class_id, class_name in config['classes'].items():
            readme_content += f"- {class_id}: {class_name}\n"
        
        readme_content += f"""
## Usage
To use this model, place the trained weights file at:
```
{config['model_path']}
```

## Environment Variables
You can override the default configuration using these environment variables:
- `SLD_MODEL_PATH`: Path to the model weights file
- `SLD_CONFIDENCE_THRESHOLD`: Detection confidence threshold (0.0-1.0)
- `SLD_IOU_THRESHOLD`: IoU threshold for NMS (0.0-1.0)

## Training Data
This model should be trained on Single Line Diagram (SLD) images containing electrical components.
The training data should include proper annotations for all supported component classes.
"""
        
        readme_path = self.models_dir / f"{model_name}_README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        logger.info(f"Created model info file: {readme_path}")

# Global configuration instance
model_config = ModelConfig()
