"""
Training script for electrical component detection model.
Trains YOLO model specifically for SLD electrical components.
"""

import os
import sys
import yaml
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ElectricalModelTrainer:
    """Trainer for electrical component detection model."""
    
    def __init__(self, 
                 data_dir: str = "electrical_training/data",
                 config_dir: str = "electrical_training/configs",
                 output_dir: str = "electrical_training/models"):
        
        self.data_dir = Path(data_dir)
        self.config_dir = Path(config_dir)
        self.output_dir = Path(output_dir)
        
        # Create directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Electrical component classes (23 core SLD components)
        self.electrical_classes = {
            0: 'HRC FUSE',
            1: 'CIRCUIT BREAKER',
            2: 'ISOLATOR',
            3: 'CONTACTOR',
            4: 'PUB kWh METER',
            5: 'CABLE TERMINATION BOX',
            6: 'RIPPLE CONTROL RECEIVER RELAY',
            7: 'PHASE SELECTOR SWITCH',
            8: 'VOLTMETER',
            9: 'AMMETER',
            10: 'CURRENT TRANSFORMER',
            11: 'THREE PHASE FUSED TAP-OFF UNIT',
            12: 'PHASE INDICATOR LIGHTS',
            13: 'SINGLE PHASE UNFUSED TAP-OFF UNIT',
            14: 'HOUSE SERVICE/METER BOARD',
            15: 'MAXIMUM DEMAND AMMETER',
            16: 'TIME DELAY RELAY',
            17: 'SINGLE PHASE TAP-OFF UNIT',
            18: 'EARTH FAULT RELAY',
            19: 'INVERSE DEFINITE MINIMUM TIME LAG OVERCURRENT RELAY',
            20: 'OVER CURRENT RELAY',
            21: 'KEY INTERLOCK BETWEEN COUPLER',
            22: 'EARTH ELECTRODE'
        }
    
    def create_dataset_config(self) -> str:
        """Create YOLO dataset configuration file."""
        
        config = {
            'path': str(self.data_dir.absolute()),
            'train': 'train/images',
            'val': 'val/images',
            'test': 'test/images',
            'nc': len(self.electrical_classes),
            'names': list(self.electrical_classes.values())
        }
        
        config_path = self.config_dir / "electrical_dataset.yaml"
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        logger.info(f"Dataset config created: {config_path}")
        return str(config_path)
    
    def create_training_config(self, 
                             model_size: str = "yolo11x",
                             epochs: int = 100,
                             batch_size: int = 16,
                             img_size: int = 640) -> str:
        """Create training configuration."""
        
        config = {
            'model': f"{model_size}.pt",
            'data': str(self.config_dir / "electrical_dataset.yaml"),
            'epochs': epochs,
            'batch': batch_size,
            'imgsz': img_size,
            'device': 'auto',  # Use GPU if available
            'workers': 8,
            'project': str(self.output_dir),
            'name': f'electrical_components_{model_size}',
            'save_period': 10,
            'patience': 20,
            'cache': True,
            'augment': True,
            'mosaic': 1.0,
            'mixup': 0.1,
            'copy_paste': 0.1,
            'degrees': 10.0,
            'translate': 0.1,
            'scale': 0.5,
            'shear': 2.0,
            'perspective': 0.0,
            'flipud': 0.0,
            'fliplr': 0.5,
            'hsv_h': 0.015,
            'hsv_s': 0.7,
            'hsv_v': 0.4
        }
        
        config_path = self.config_dir / f"training_config_{model_size}.yaml"
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        logger.info(f"Training config created: {config_path}")
        return str(config_path)
    
    def prepare_dataset_structure(self):
        """Prepare the dataset directory structure."""
        
        splits = ['train', 'val', 'test']
        subdirs = ['images', 'labels']
        
        for split in splits:
            for subdir in subdirs:
                dir_path = self.data_dir / split / subdir
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
        
        # Create classes.txt file
        classes_file = self.data_dir / "classes.txt"
        with open(classes_file, 'w') as f:
            for class_name in self.electrical_classes.values():
                f.write(f"{class_name}\n")
        
        logger.info(f"Classes file created: {classes_file}")
    
    def validate_dataset(self) -> Dict[str, Any]:
        """Validate the dataset structure and content."""
        
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        # Check directory structure
        required_dirs = [
            'train/images', 'train/labels',
            'val/images', 'val/labels',
            'test/images', 'test/labels'
        ]
        
        for dir_name in required_dirs:
            dir_path = self.data_dir / dir_name
            if not dir_path.exists():
                validation_results['errors'].append(f"Missing directory: {dir_path}")
                validation_results['valid'] = False
        
        # Count files in each split
        for split in ['train', 'val', 'test']:
            images_dir = self.data_dir / split / 'images'
            labels_dir = self.data_dir / split / 'labels'
            
            if images_dir.exists() and labels_dir.exists():
                image_files = list(images_dir.glob('*.jpg')) + list(images_dir.glob('*.png'))
                label_files = list(labels_dir.glob('*.txt'))
                
                validation_results['statistics'][split] = {
                    'images': len(image_files),
                    'labels': len(label_files)
                }
                
                # Check if image and label counts match
                if len(image_files) != len(label_files):
                    validation_results['warnings'].append(
                        f"{split}: Image count ({len(image_files)}) != Label count ({len(label_files)})"
                    )
        
        return validation_results
    
    def train_model(self, 
                   model_size: str = "yolo11x",
                   epochs: int = 100,
                   batch_size: int = 16,
                   resume: bool = False) -> str:
        """Train the electrical component detection model."""
        
        try:
            from ultralytics import YOLO
        except ImportError:
            logger.error("Ultralytics YOLO not installed. Install with: pip install ultralytics")
            return None
        
        # Validate dataset first
        validation = self.validate_dataset()
        if not validation['valid']:
            logger.error("Dataset validation failed:")
            for error in validation['errors']:
                logger.error(f"  - {error}")
            return None
        
        # Create configs
        dataset_config = self.create_dataset_config()
        training_config = self.create_training_config(model_size, epochs, batch_size)
        
        # Initialize model
        model = YOLO(f"{model_size}.pt")
        
        # Train the model
        logger.info(f"Starting training with {model_size} model...")
        logger.info(f"Dataset: {dataset_config}")
        logger.info(f"Epochs: {epochs}, Batch size: {batch_size}")
        
        results = model.train(
            data=dataset_config,
            epochs=epochs,
            batch=batch_size,
            imgsz=640,
            device='auto',
            project=str(self.output_dir),
            name=f'electrical_components_{model_size}',
            resume=resume
        )
        
        # Save the trained model
        model_path = self.output_dir / f'electrical_components_{model_size}' / 'weights' / 'best.pt'
        
        if model_path.exists():
            # Copy to main models directory
            final_model_path = self.output_dir / f'electrical_components_{model_size}_best.pt'
            shutil.copy2(model_path, final_model_path)
            logger.info(f"Model saved to: {final_model_path}")
            return str(final_model_path)
        else:
            logger.error("Training completed but model file not found")
            return None
    
    def evaluate_model(self, model_path: str) -> Dict[str, Any]:
        """Evaluate the trained model."""
        
        try:
            from ultralytics import YOLO
        except ImportError:
            logger.error("Ultralytics YOLO not installed")
            return {}
        
        if not os.path.exists(model_path):
            logger.error(f"Model file not found: {model_path}")
            return {}
        
        # Load model
        model = YOLO(model_path)
        
        # Evaluate on test set
        dataset_config = self.config_dir / "electrical_dataset.yaml"
        
        if dataset_config.exists():
            results = model.val(data=str(dataset_config), split='test')
            
            return {
                'mAP50': results.box.map50,
                'mAP50-95': results.box.map,
                'precision': results.box.mp,
                'recall': results.box.mr,
                'f1_score': 2 * (results.box.mp * results.box.mr) / (results.box.mp + results.box.mr)
            }
        else:
            logger.error("Dataset config not found for evaluation")
            return {}
    
    def export_model(self, model_path: str, format: str = 'onnx') -> str:
        """Export model to different formats."""
        
        try:
            from ultralytics import YOLO
        except ImportError:
            logger.error("Ultralytics YOLO not installed")
            return None
        
        if not os.path.exists(model_path):
            logger.error(f"Model file not found: {model_path}")
            return None
        
        # Load and export model
        model = YOLO(model_path)
        exported_path = model.export(format=format)
        
        logger.info(f"Model exported to {format}: {exported_path}")
        return exported_path

def main():
    """Main training function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Train electrical component detection model")
    parser.add_argument("--model", default="yolo11x", choices=["yolo11n", "yolo11s", "yolo11m", "yolo11l", "yolo11x"],
                       help="YOLO model size")
    parser.add_argument("--epochs", type=int, default=100, help="Number of training epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--resume", action="store_true", help="Resume training from checkpoint")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate model after training")
    parser.add_argument("--export", choices=["onnx", "tensorrt", "coreml"], help="Export model format")
    
    args = parser.parse_args()
    
    # Initialize trainer
    trainer = ElectricalModelTrainer()
    
    # Prepare dataset structure
    trainer.prepare_dataset_structure()
    
    # Validate dataset
    validation = trainer.validate_dataset()
    print(f"Dataset validation: {'✅ PASSED' if validation['valid'] else '❌ FAILED'}")
    
    if validation['errors']:
        print("Errors:")
        for error in validation['errors']:
            print(f"  - {error}")
    
    if validation['warnings']:
        print("Warnings:")
        for warning in validation['warnings']:
            print(f"  - {warning}")
    
    print("Dataset statistics:")
    for split, stats in validation['statistics'].items():
        print(f"  {split}: {stats['images']} images, {stats['labels']} labels")
    
    if not validation['valid']:
        print("Please fix dataset issues before training")
        return
    
    # Train model
    print(f"\n🚀 Starting training with {args.model} model...")
    model_path = trainer.train_model(
        model_size=args.model,
        epochs=args.epochs,
        batch_size=args.batch,
        resume=args.resume
    )
    
    if model_path:
        print(f"✅ Training completed! Model saved to: {model_path}")
        
        # Evaluate if requested
        if args.evaluate:
            print("\n📊 Evaluating model...")
            metrics = trainer.evaluate_model(model_path)
            if metrics:
                print("Evaluation metrics:")
                for metric, value in metrics.items():
                    print(f"  {metric}: {value:.4f}")
        
        # Export if requested
        if args.export:
            print(f"\n📦 Exporting model to {args.export}...")
            exported_path = trainer.export_model(model_path, args.export)
            if exported_path:
                print(f"✅ Model exported to: {exported_path}")
    else:
        print("❌ Training failed!")

if __name__ == "__main__":
    main()
