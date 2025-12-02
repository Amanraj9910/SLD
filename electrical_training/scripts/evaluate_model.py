#!/usr/bin/env python3
"""
Model Evaluation Script for Electrical Components Detection
Comprehensive evaluation with metrics and visualizations
"""

import argparse
import yaml
from pathlib import Path
import json
import time
from datetime import datetime

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    print("⚠️ Ultralytics not available. Please install: pip install ultralytics")
    YOLO_AVAILABLE = False

class ElectricalEvaluator:
    """Comprehensive evaluator for electrical components models"""
    
    def __init__(self, model_path: str, data_config: str = None):
        self.base_dir = Path(__file__).parent.parent
        self.model_path = Path(model_path)
        self.results_dir = self.base_dir / "results" / "metrics"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Load model
        if YOLO_AVAILABLE and self.model_path.exists():
            self.model = YOLO(str(self.model_path))
            print(f"✅ Loaded model: {self.model_path}")
        else:
            self.model = None
            print(f"❌ Could not load model: {self.model_path}")
        
        # Data configuration
        if data_config is None:
            data_config = self.base_dir / "data" / "processed" / "electrical_components" / "data.yaml"
        
        self.data_config = str(data_config) if Path(data_config).exists() else None
        
        # Class names
        self.class_names = {
            0: "CIRCUIT BREAKER",
            1: "HRC FUSE", 
            2: "ISOLATOR"
        }
    
    def evaluate_model(self) -> dict:
        """Comprehensive model evaluation"""
        if not self.model or not self.data_config:
            print("❌ Model or data config not available")
            return {}
        
        print("🔍 Starting Model Evaluation")
        print("=" * 50)
        
        try:
            # Run validation
            results = self.model.val(
                data=self.data_config,
                save_json=True,
                save_hybrid=False,
                conf=0.001,
                iou=0.6,
                max_det=300,
                half=False,
                device='cpu',
                plots=True,
                verbose=True
            )
            
            # Extract metrics
            metrics = self._extract_metrics(results)
            
            # Save detailed results
            self._save_results(metrics)
            
            # Print summary
            self._print_summary(metrics)
            
            return metrics
            
        except Exception as e:
            print(f"❌ Evaluation failed: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return {}
    
    def _extract_metrics(self, results) -> dict:
        """Extract detailed metrics from validation results"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'model_path': str(self.model_path),
            'overall_metrics': {},
            'class_metrics': {},
            'performance': {}
        }
        
        try:
            # Overall metrics
            if hasattr(results, 'box'):
                box_metrics = results.box
                metrics['overall_metrics'] = {
                    'map50': float(box_metrics.map50) if hasattr(box_metrics, 'map50') else 0.0,
                    'map50_95': float(box_metrics.map) if hasattr(box_metrics, 'map') else 0.0,
                    'precision': float(box_metrics.mp) if hasattr(box_metrics, 'mp') else 0.0,
                    'recall': float(box_metrics.mr) if hasattr(box_metrics, 'mr') else 0.0,
                    'f1_score': 0.0  # Will calculate below
                }
                
                # Calculate F1 score
                p = metrics['overall_metrics']['precision']
                r = metrics['overall_metrics']['recall']
                if p + r > 0:
                    metrics['overall_metrics']['f1_score'] = 2 * (p * r) / (p + r)
            
            # Per-class metrics
            if hasattr(results, 'box') and hasattr(results.box, 'ap_class_index'):
                class_indices = results.box.ap_class_index
                if hasattr(results.box, 'ap50'):
                    ap50_per_class = results.box.ap50
                    for i, class_idx in enumerate(class_indices):
                        class_name = self.class_names.get(int(class_idx), f"class_{class_idx}")
                        metrics['class_metrics'][class_name] = {
                            'ap50': float(ap50_per_class[i]) if i < len(ap50_per_class) else 0.0,
                            'class_id': int(class_idx)
                        }
            
            # Performance metrics (if available)
            if hasattr(results, 'speed'):
                speed = results.speed
                metrics['performance'] = {
                    'preprocess_time': float(speed.get('preprocess', 0)),
                    'inference_time': float(speed.get('inference', 0)),
                    'postprocess_time': float(speed.get('postprocess', 0)),
                    'total_time': float(speed.get('preprocess', 0) + speed.get('inference', 0) + speed.get('postprocess', 0))
                }
        
        except Exception as e:
            print(f"⚠️ Error extracting metrics: {e}")
        
        return metrics
    
    def _save_results(self, metrics: dict):
        """Save evaluation results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"evaluation_{timestamp}.json"
        
        try:
            with open(results_file, 'w') as f:
                json.dump(metrics, f, indent=2)
            print(f"✅ Results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️ Could not save results: {e}")
    
    def _print_summary(self, metrics: dict):
        """Print evaluation summary"""
        print("\n📊 Evaluation Summary")
        print("=" * 50)
        
        overall = metrics.get('overall_metrics', {})
        print(f"🎯 Overall Performance:")
        print(f"   mAP@0.5:     {overall.get('map50', 0):.3f}")
        print(f"   mAP@0.5:0.95: {overall.get('map50_95', 0):.3f}")
        print(f"   Precision:   {overall.get('precision', 0):.3f}")
        print(f"   Recall:      {overall.get('recall', 0):.3f}")
        print(f"   F1 Score:    {overall.get('f1_score', 0):.3f}")
        
        class_metrics = metrics.get('class_metrics', {})
        if class_metrics:
            print(f"\n🏷️ Per-Class Performance (AP@0.5):")
            for class_name, class_data in class_metrics.items():
                ap50 = class_data.get('ap50', 0)
                print(f"   {class_name:15}: {ap50:.3f}")
        
        performance = metrics.get('performance', {})
        if performance:
            print(f"\n⚡ Performance Metrics:")
            print(f"   Inference Time: {performance.get('inference_time', 0):.1f} ms")
            print(f"   Total Time:     {performance.get('total_time', 0):.1f} ms")
        
        # Performance assessment
        self._assess_performance(metrics)
    
    def _assess_performance(self, metrics: dict):
        """Assess model performance and provide recommendations"""
        print(f"\n🎯 Performance Assessment:")
        
        overall = metrics.get('overall_metrics', {})
        map50 = overall.get('map50', 0)
        precision = overall.get('precision', 0)
        recall = overall.get('recall', 0)
        
        # Overall assessment
        if map50 >= 0.9:
            print("   ✅ EXCELLENT: Model performance is outstanding!")
        elif map50 >= 0.8:
            print("   ✅ GOOD: Model performance is very good")
        elif map50 >= 0.7:
            print("   ⚠️ FAIR: Model performance is acceptable but could be improved")
        else:
            print("   ❌ POOR: Model needs significant improvement")
        
        # Specific recommendations
        print(f"\n💡 Recommendations:")
        
        if map50 < 0.8:
            print("   • Consider training for more epochs")
            print("   • Try data augmentation techniques")
            print("   • Check dataset quality and annotations")
        
        if precision < 0.8:
            print("   • High false positive rate - consider increasing confidence threshold")
            print("   • Review and clean training data")
        
        if recall < 0.8:
            print("   • High false negative rate - consider lowering confidence threshold")
            print("   • Add more training examples for missed components")
        
        # Class-specific recommendations
        class_metrics = metrics.get('class_metrics', {})
        worst_class = None
        worst_ap = 1.0
        
        for class_name, class_data in class_metrics.items():
            ap50 = class_data.get('ap50', 0)
            if ap50 < worst_ap:
                worst_ap = ap50
                worst_class = class_name
        
        if worst_class and worst_ap < 0.7:
            print(f"   • {worst_class} has lowest performance ({worst_ap:.3f}) - needs more training data")
    
    def benchmark_inference(self, num_images: int = 100) -> dict:
        """Benchmark inference speed"""
        if not self.model:
            return {}
        
        print(f"\n⚡ Benchmarking Inference Speed ({num_images} images)")
        print("=" * 50)
        
        # Create dummy images for benchmarking
        import numpy as np
        dummy_images = [np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8) for _ in range(num_images)]
        
        # Warm up
        for _ in range(5):
            self.model(dummy_images[0], verbose=False)
        
        # Benchmark
        start_time = time.time()
        for img in dummy_images:
            self.model(img, verbose=False)
        total_time = time.time() - start_time
        
        avg_time = (total_time / num_images) * 1000  # ms per image
        fps = num_images / total_time
        
        benchmark_results = {
            'total_time': total_time,
            'avg_inference_time_ms': avg_time,
            'fps': fps,
            'num_images': num_images
        }
        
        print(f"   Average inference time: {avg_time:.1f} ms")
        print(f"   Frames per second: {fps:.1f} FPS")
        
        return benchmark_results

def main():
    """Main evaluation function"""
    parser = argparse.ArgumentParser(description='Evaluate Electrical Components Detection Model')
    parser.add_argument('--model', type=str, required=True, help='Path to model file (.pt)')
    parser.add_argument('--data', type=str, help='Path to data config file')
    parser.add_argument('--benchmark', action='store_true', help='Run inference speed benchmark')
    
    args = parser.parse_args()
    
    if not YOLO_AVAILABLE:
        print("❌ Please install ultralytics: pip install ultralytics")
        return
    
    # Initialize evaluator
    evaluator = ElectricalEvaluator(args.model, args.data)
    
    # Run evaluation
    metrics = evaluator.evaluate_model()
    
    # Run benchmark if requested
    if args.benchmark:
        benchmark_results = evaluator.benchmark_inference()
        metrics['benchmark'] = benchmark_results
    
    if metrics:
        print(f"\n🎉 Evaluation completed successfully!")
        print(f"📁 Results saved in: {evaluator.results_dir}")
    else:
        print(f"\n❌ Evaluation failed!")

if __name__ == "__main__":
    main()
