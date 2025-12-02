#!/usr/bin/env python3
"""
Data Preparation Script for Electrical Components Training
Finds, processes, and organizes training data from various sources
"""

import os
import shutil
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
import random
try:
    from PIL import Image
except ImportError:
    print("PIL not available, image processing will be limited")
import json

class ElectricalDataPreparator:
    """Prepare electrical components data for training"""
    
    def __init__(self, config_path: str = None):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.config = self._load_config(config_path)
        
        # Create directory structure
        self._create_directories()
        
    def _load_config(self, config_path: str = None) -> Dict:
        """Load data configuration"""
        if config_path is None:
            config_path = self.base_dir / "configs" / "data_configs" / "electrical_components.yaml"
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _create_directories(self):
        """Create necessary directory structure"""
        dirs = [
            self.data_dir / "raw",
            self.data_dir / "processed" / "electrical_components" / "images" / "train",
            self.data_dir / "processed" / "electrical_components" / "images" / "val", 
            self.data_dir / "processed" / "electrical_components" / "images" / "test",
            self.data_dir / "processed" / "electrical_components" / "labels" / "train",
            self.data_dir / "processed" / "electrical_components" / "labels" / "val",
            self.data_dir / "processed" / "electrical_components" / "labels" / "test",
            self.data_dir / "augmented",
            self.data_dir / "splits"
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        print(f"✅ Created directory structure in {self.data_dir}")
    
    def find_existing_datasets(self) -> List[Path]:
        """Find existing electrical component datasets"""
        search_paths = [
            # Look for your existing datasets
            Path("../../YOLO/sld_yolov8_project/datasets/sld_components_v1"),
            Path("../../SLD-New/YOLO/datasets/multiclass"),
            Path("../../SLD-YOLO/dataset"),
            Path("../../../YOLO/sld_yolov8_project/datasets/sld_components_v1"),
            Path("../../../SLD-New/YOLO/datasets/multiclass"),
            Path("../../../SLD-YOLO/dataset"),
            Path("../../../../YOLO/sld_yolov8_project/datasets/sld_components_v1"),
            Path("../../../../SLD-New/YOLO/datasets/multiclass"),
        ]
        
        found_datasets = []
        for path in search_paths:
            abs_path = (self.base_dir / path).resolve()
            if abs_path.exists():
                found_datasets.append(abs_path)
                print(f"✅ Found dataset: {abs_path}")
        
        return found_datasets
    
    def copy_dataset(self, source_path: Path) -> bool:
        """Copy dataset to training folder"""
        try:
            print(f"📁 Copying dataset from {source_path}")
            
            # Look for images and labels
            image_dirs = list(source_path.rglob("**/images"))
            label_dirs = list(source_path.rglob("**/labels"))
            
            if not image_dirs:
                print(f"⚠️ No images directory found in {source_path}")
                return False
            
            # Copy images and labels
            for img_dir in image_dirs:
                if "train" in str(img_dir):
                    self._copy_files(img_dir, self.data_dir / "processed" / "electrical_components" / "images" / "train")
                elif "val" in str(img_dir):
                    self._copy_files(img_dir, self.data_dir / "processed" / "electrical_components" / "images" / "val")
                else:
                    # Copy to train by default
                    self._copy_files(img_dir, self.data_dir / "processed" / "electrical_components" / "images" / "train")
            
            for label_dir in label_dirs:
                if "train" in str(label_dir):
                    self._copy_files(label_dir, self.data_dir / "processed" / "electrical_components" / "labels" / "train")
                elif "val" in str(label_dir):
                    self._copy_files(label_dir, self.data_dir / "processed" / "electrical_components" / "labels" / "val")
                else:
                    # Copy to train by default
                    self._copy_files(label_dir, self.data_dir / "processed" / "electrical_components" / "labels" / "train")
            
            return True
            
        except Exception as e:
            print(f"❌ Error copying dataset: {e}")
            return False
    
    def _copy_files(self, source_dir: Path, target_dir: Path):
        """Copy files from source to target directory"""
        if not source_dir.exists():
            return
            
        target_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path in source_dir.iterdir():
            if file_path.is_file():
                target_file = target_dir / file_path.name
                if not target_file.exists():
                    shutil.copy2(file_path, target_file)
    
    def create_data_yaml(self):
        """Create data.yaml file for training"""
        data_config = {
            'path': str((self.data_dir / "processed" / "electrical_components").absolute()),
            'train': 'images/train',
            'val': 'images/val',
            'test': 'images/test',
            'nc': 3,
            'names': {
                0: 'CIRCUIT BREAKER',
                1: 'HRC FUSE', 
                2: 'ISOLATOR'
            }
        }
        
        yaml_path = self.data_dir / "processed" / "electrical_components" / "data.yaml"
        with open(yaml_path, 'w') as f:
            yaml.dump(data_config, f, default_flow_style=False)
        
        print(f"✅ Created data.yaml at {yaml_path}")
        return yaml_path
    
    def analyze_dataset(self) -> Dict:
        """Analyze the prepared dataset"""
        stats = {
            'train_images': 0,
            'val_images': 0,
            'test_images': 0,
            'train_labels': 0,
            'val_labels': 0,
            'test_labels': 0,
            'class_distribution': {0: 0, 1: 0, 2: 0}
        }
        
        # Count files
        for split in ['train', 'val', 'test']:
            img_dir = self.data_dir / "processed" / "electrical_components" / "images" / split
            label_dir = self.data_dir / "processed" / "electrical_components" / "labels" / split
            
            if img_dir.exists():
                stats[f'{split}_images'] = len(list(img_dir.glob('*.jpg')) + list(img_dir.glob('*.png')))
            
            if label_dir.exists():
                stats[f'{split}_labels'] = len(list(label_dir.glob('*.txt')))
                
                # Count class distribution
                for label_file in label_dir.glob('*.txt'):
                    try:
                        with open(label_file, 'r') as f:
                            for line in f:
                                if line.strip():
                                    class_id = int(line.split()[0])
                                    if class_id in stats['class_distribution']:
                                        stats['class_distribution'][class_id] += 1
                    except:
                        continue
        
        return stats
    
    def prepare_data(self):
        """Main data preparation pipeline"""
        print("🔧 Starting Electrical Components Data Preparation")
        print("=" * 60)
        
        # Find existing datasets
        datasets = self.find_existing_datasets()
        
        if not datasets:
            print("❌ No existing datasets found!")
            print("Please ensure your training data is available in one of the expected locations.")
            return False
        
        # Copy the first found dataset
        success = self.copy_dataset(datasets[0])
        
        if not success:
            print("❌ Failed to copy dataset")
            return False
        
        # Create data.yaml
        yaml_path = self.create_data_yaml()
        
        # Analyze dataset
        stats = self.analyze_dataset()
        
        print("\n📊 Dataset Statistics:")
        print(f"   Training images: {stats['train_images']}")
        print(f"   Validation images: {stats['val_images']}")
        print(f"   Test images: {stats['test_images']}")
        print(f"   Training labels: {stats['train_labels']}")
        print(f"   Validation labels: {stats['val_labels']}")
        print(f"   Test labels: {stats['test_labels']}")
        print(f"\n🏷️ Class Distribution:")
        print(f"   CIRCUIT BREAKER: {stats['class_distribution'][0]}")
        print(f"   HRC FUSE: {stats['class_distribution'][1]}")
        print(f"   ISOLATOR: {stats['class_distribution'][2]}")
        
        print(f"\n✅ Data preparation completed!")
        print(f"📁 Dataset ready at: {self.data_dir / 'processed' / 'electrical_components'}")
        print(f"📄 Configuration file: {yaml_path}")
        
        return True

def main():
    """Main function"""
    preparator = ElectricalDataPreparator()
    success = preparator.prepare_data()
    
    if success:
        print("\n🚀 Ready for training!")
        print("Next steps:")
        print("1. Run: python scripts/train_model.py")
        print("2. Monitor training in results/experiments/")
        print("3. Evaluate model with scripts/evaluate_model.py")
    else:
        print("\n❌ Data preparation failed!")

if __name__ == "__main__":
    main()
