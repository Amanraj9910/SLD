#!/usr/bin/env python3
"""
Advanced Training Script for Electrical Components Detection
Implements multiple training strategies and best practices
"""

import argparse
import yaml
from pathlib import Path
import time
import sys
from datetime import datetime

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    print("⚠️ Ultralytics not available. Please install: pip install ultralytics")
    YOLO_AVAILABLE = False

class ElectricalTrainer:
    """Advanced trainer for electrical components detection"""
    
    def __init__(self, config_path: str = None):
        self.base_dir = Path(__file__).parent.parent
        self.config = self._load_config(config_path)
        self.results_dir = self.base_dir / "results" / "experiments"
        self.models_dir = self.base_dir / "models"
        
        # Create directories
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        (self.models_dir / "checkpoints").mkdir(exist_ok=True)
        (self.models_dir / "best").mkdir(exist_ok=True)
        (self.models_dir / "production").mkdir(exist_ok=True)
    
    def _load_config(self, config_path: str = None) -> dict:
        """Load training configuration"""
        if config_path is None:
            config_path = self.base_dir / "configs" / "training_configs" / "electrical_v1.yaml"
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def download_pretrained_models(self):
        """Download required pretrained models"""
        if not YOLO_AVAILABLE:
            print("❌ Cannot download models - ultralytics not available")
            return False
        
        pretrained_dir = self.models_dir / "pretrained"
        pretrained_dir.mkdir(exist_ok=True)
        
        # Latest YOLOv11 models for best performance
        models = ['yolo11n.pt', 'yolo11s.pt', 'yolo11m.pt', 'yolo11l.pt', 'yolo11x.pt']
        
        print("📥 Downloading pretrained models...")
        for model_name in models:
            try:
                model_path = pretrained_dir / model_name
                if not model_path.exists():
                    print(f"   Downloading {model_name}...")
                    model = YOLO(model_name)
                    # The model is automatically downloaded and cached
                    print(f"   ✅ {model_name} ready")
                else:
                    print(f"   ✅ {model_name} already exists")
            except Exception as e:
                print(f"   ❌ Failed to download {model_name}: {e}")
        
        return True
    
    def prepare_data_config(self) -> str:
        """Prepare data configuration file"""
        data_config_path = self.base_dir / "data" / "processed" / "electrical_components" / "data.yaml"
        
        if not data_config_path.exists():
            print("❌ Data configuration not found!")
            print("Please run: python scripts/data_preparation.py")
            return None
        
        return str(data_config_path)
    
    def train_progressive(self) -> dict:
        """Progressive training strategy: Start fast, then accurate"""
        if not YOLO_AVAILABLE:
            print("❌ Cannot train - ultralytics not available")
            return {}
        
        print("🚀 Starting Progressive Training Strategy")
        print("=" * 60)
        
        data_config = self.prepare_data_config()
        if not data_config:
            return {}
        
        results = {}
        
        # Stage 1: Fast training with YOLO11s
        print("\n📍 Stage 1: Fast Training (YOLO11s)")
        try:
            model_s = YOLO('yolo11s.pt')
            results_s = model_s.train(
                data=data_config,
                epochs=50,
                imgsz=640,
                batch=16,
                patience=25,
                name='electrical_stage1_fast',
                project=str(self.results_dir),
                save=True,
                verbose=True,
                device=self.config['device']
            )
            results['stage1'] = results_s
            print("✅ Stage 1 completed")
        except Exception as e:
            print(f"❌ Stage 1 failed: {e}")
            return {}
        
        # Stage 2: Accurate training with YOLO11x
        print("\n📍 Stage 2: Accurate Training (YOLO11x)")
        try:
            model_x = YOLO('yolo11x.pt')
            results_x = model_x.train(
                data=data_config,
                epochs=self.config['training']['epochs'],
                imgsz=self.config['training']['image_size'],
                batch=self.config['training']['batch_size'],
                patience=self.config['training']['patience'],
                name='electrical_stage2_accurate',
                project=str(self.results_dir),
                save=True,
                verbose=True,
                device=self.config['device'],
                lr0=self.config['training']['lr0'],
                lrf=self.config['training']['lrf'],
                momentum=self.config['training']['momentum'],
                weight_decay=self.config['training']['weight_decay'],
                warmup_epochs=self.config['training']['warmup_epochs']
            )
            results['stage2'] = results_x
            print("✅ Stage 2 completed")
        except Exception as e:
            print(f"❌ Stage 2 failed: {e}")
            return results
        
        return results
    
    def train_single_model(self, model_name: str = None) -> dict:
        """Train a single model with optimal settings"""
        if not YOLO_AVAILABLE:
            print("❌ Cannot train - ultralytics not available")
            return {}
        
        if model_name is None:
            model_name = self.config['model']['architecture']
        
        print(f"🚀 Training Single Model: {model_name}")
        print("=" * 60)
        
        data_config = self.prepare_data_config()
        if not data_config:
            return {}
        
        try:
            # Load model
            model = YOLO(f'{model_name}.pt')
            
            # Train with full configuration
            results = model.train(
                data=data_config,
                epochs=self.config['training']['epochs'],
                imgsz=self.config['training']['image_size'],
                batch=self.config['training']['batch_size'],
                patience=self.config['training']['patience'],
                name=f'electrical_{model_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                project=str(self.results_dir),
                save=True,
                verbose=True,
                device=self.config['device'],
                
                # Learning rate settings
                lr0=self.config['training']['lr0'],
                lrf=self.config['training']['lrf'],
                momentum=self.config['training']['momentum'],
                weight_decay=self.config['training']['weight_decay'],
                warmup_epochs=self.config['training']['warmup_epochs'],
                warmup_momentum=self.config['training']['warmup_momentum'],
                warmup_bias_lr=self.config['training']['warmup_bias_lr'],
                
                # Loss weights
                box=self.config['loss']['box'],
                cls=self.config['loss']['cls'],
                dfl=self.config['loss']['dfl'],
                
                # Augmentation
                degrees=self.config['augmentation']['degrees'],
                translate=self.config['augmentation']['translate'],
                scale=self.config['augmentation']['scale'],
                shear=self.config['augmentation']['shear'],
                perspective=self.config['augmentation']['perspective'],
                hsv_h=self.config['augmentation']['hsv_h'],
                hsv_s=self.config['augmentation']['hsv_s'],
                hsv_v=self.config['augmentation']['hsv_v'],
                mosaic=self.config['augmentation']['mosaic'],
                mixup=self.config['augmentation']['mixup'],
                copy_paste=self.config['augmentation']['copy_paste'],
                
                # Validation
                val=True,
                save_json=self.config['validation']['save_json'],
                conf=self.config['validation']['conf_threshold'],
                iou=self.config['validation']['iou_threshold'],
                max_det=self.config['validation']['max_detections'],
                
                # Hardware
                amp=self.config['amp'],
                deterministic=self.config['deterministic'],
                seed=self.config['seed']
            )
            
            print("✅ Training completed successfully!")
            return {'single_model': results}
            
        except Exception as e:
            print(f"❌ Training failed: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return {}
    
    def save_best_model(self, results: dict):
        """Save the best performing model"""
        if not results:
            return
        
        try:
            # Find the best model from results
            best_model_path = None
            best_map = 0
            
            for stage, result in results.items():
                if hasattr(result, 'box') and hasattr(result.box, 'map50'):
                    if result.box.map50 > best_map:
                        best_map = result.box.map50
                        # Find the weights file
                        exp_dir = self.results_dir / result.save_dir.name if hasattr(result, 'save_dir') else None
                        if exp_dir and exp_dir.exists():
                            weights_dir = exp_dir / "weights"
                            if weights_dir.exists():
                                best_model_path = weights_dir / "best.pt"
            
            if best_model_path and best_model_path.exists():
                # Copy to production directory
                production_path = self.models_dir / "production" / "electrical_components_best.pt"
                import shutil
                shutil.copy2(best_model_path, production_path)
                print(f"✅ Best model saved to: {production_path}")
                print(f"   Best mAP@0.5: {best_map:.3f}")
            
        except Exception as e:
            print(f"⚠️ Could not save best model: {e}")

def main():
    """Main training function"""
    parser = argparse.ArgumentParser(description='Train Electrical Components Detection Model')
    parser.add_argument('--config', type=str, help='Path to training config file')
    parser.add_argument('--strategy', type=str, choices=['progressive', 'single'], 
                       default='single', help='Training strategy')
    parser.add_argument('--model', type=str, choices=['yolo11n', 'yolo11s', 'yolo11m', 'yolo11l', 'yolo11x'],
                       default='yolo11x', help='YOLO11 model architecture')
    
    args = parser.parse_args()
    
    if not YOLO_AVAILABLE:
        print("❌ Please install ultralytics: pip install ultralytics")
        sys.exit(1)
    
    # Initialize trainer
    trainer = ElectricalTrainer(args.config)
    
    # Download pretrained models
    trainer.download_pretrained_models()
    
    # Start training
    start_time = time.time()
    
    if args.strategy == 'progressive':
        results = trainer.train_progressive()
    else:
        results = trainer.train_single_model(args.model)
    
    training_time = time.time() - start_time
    
    # Save best model
    trainer.save_best_model(results)
    
    print(f"\n🎉 Training completed in {training_time/3600:.2f} hours")
    print(f"📁 Results saved in: {trainer.results_dir}")
    print(f"🏆 Best model: {trainer.models_dir / 'production' / 'electrical_components_best.pt'}")

if __name__ == "__main__":
    main()
