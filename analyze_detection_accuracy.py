#!/usr/bin/env python3
"""
Analyze YOLO model detection accuracy issues for specific component classes
"""

import sys
import os
from pathlib import Path
import tempfile
from PIL import Image, ImageDraw

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent / "web_app" / "core" / "backend"
sys.path.insert(0, str(backend_dir))

# Ensure the backend directory exists
if not backend_dir.exists():
    print(f"❌ Backend directory not found: {backend_dir}")
    sys.exit(1)

def analyze_detection_parameters():
    """Analyze current detection parameters and their impact"""
    print("🔍 Analyzing Detection Parameters...")
    print("=" * 60)
    
    try:
        os.chdir(backend_dir)

        # Import with explicit error handling
        try:
            from utils.config import get_settings  # type: ignore
        except ImportError as e:
            print(f"❌ Failed to import utils.config: {e}")
            print(f"   Current working directory: {os.getcwd()}")
            print(f"   Python path: {sys.path[:3]}...")
            return False
        
        settings = get_settings()
        
        print(f"📋 Current Configuration:")
        print(f"  Model Path: {settings.yolo_model_path}")
        print(f"  Confidence Threshold: {settings.yolo_confidence_threshold}")
        print(f"  IoU Threshold: {settings.yolo_iou_threshold}")
        
        # Test with different confidence thresholds
        print(f"\n🧪 Testing Different Confidence Thresholds:")
        test_thresholds = [0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]
        
        for threshold in test_thresholds:
            print(f"  Threshold {threshold:.2f}: ", end="")
            if threshold < 0.1:
                print("Very low - may include noise/false positives")
            elif threshold < 0.2:
                print("Low - good for small/unclear components")
            elif threshold < 0.3:
                print("Medium - balanced detection")
            else:
                print("High - only confident detections")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

def create_test_sld_with_components():
    """Create a test SLD image with known component types"""
    print(f"\n🖼️ Creating Test SLD Image...")
    
    # Create a realistic SLD diagram
    width, height = 1200, 800
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw electrical components that should be detected
    components = []
    
    # Cable Termination Boxes (rectangular shapes)
    ctb_positions = [(200, 300), (600, 300), (1000, 300)]
    for i, (x, y) in enumerate(ctb_positions):
        # Draw rectangular box
        draw.rectangle([x-40, y-30, x+40, y+30], outline='black', width=3)
        draw.text((x-35, y-20), 'CTB', fill='black')
        components.append({
            'type': 'Cable Termination Box',
            'bbox': [x-40, y-30, x+40, y+30],
            'expected': True
        })
    
    # Single Phase Tap-Off Units (circular/oval shapes)
    tou_positions = [(300, 500), (700, 500)]
    for i, (x, y) in enumerate(tou_positions):
        # Draw circular/oval shape
        draw.ellipse([x-25, y-20, x+25, y+20], outline='black', width=3)
        draw.text((x-20, y-10), 'TOU', fill='black')
        components.append({
            'type': 'Single Phase Tap-Off Unit',
            'bbox': [x-25, y-20, x+25, y+20],
            'expected': True
        })
    
    # Add some background elements that might cause false positives
    # Text labels
    draw.text((100, 100), 'SLD DIAGRAM - ELECTRICAL COMPONENTS', fill='black')
    draw.text((100, 150), 'Main Distribution Board', fill='black')
    
    # Lines connecting components
    for i in range(len(ctb_positions)-1):
        x1, y1 = ctb_positions[i]
        x2, y2 = ctb_positions[i+1]
        draw.line([x1+40, y1, x2-40, y2], fill='black', width=2)
    
    # Vertical connections
    for (x, y) in ctb_positions:
        draw.line([x, y+30, x, y+100], fill='black', width=2)
    
    return img, components



def test_detection_with_different_parameters():
    """Test detection with various parameter combinations"""
    print(f"\n🧪 Testing Detection with Different Parameters...")
    print("=" * 60)

    try:
        os.chdir(backend_dir)

        # Import with explicit error handling
        try:
            from services.component_service import ComponentDetectionService  # type: ignore
            from utils.config import get_settings, resolve_model_path  # type: ignore
        except ImportError as e:
            print(f"❌ Failed to import required modules: {e}")
            print(f"   Current working directory: {os.getcwd()}")
            print(f"   Python path: {sys.path[:3]}...")
            return None
        
        settings = get_settings()
        model_path = resolve_model_path(settings.yolo_model_path)
        
        # Create test image
        test_img, _ = create_test_sld_with_components()
        
        # Save test image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            test_img.save(tmp_file.name)
            temp_path = tmp_file.name
        
        try:
            # Test different parameter combinations
            test_configs = [
                {'conf': 0.01, 'iou': 0.3, 'name': 'Current Settings (Very Low Conf)'},
                {'conf': 0.05, 'iou': 0.3, 'name': 'Low Confidence'},
                {'conf': 0.1, 'iou': 0.3, 'name': 'Medium-Low Confidence'},
                {'conf': 0.15, 'iou': 0.3, 'name': 'Medium Confidence'},
                {'conf': 0.2, 'iou': 0.3, 'name': 'Medium-High Confidence'},
                {'conf': 0.25, 'iou': 0.3, 'name': 'High Confidence (UI Filter)'},
                {'conf': 0.1, 'iou': 0.2, 'name': 'Lower IoU (More Overlaps)'},
                {'conf': 0.1, 'iou': 0.5, 'name': 'Higher IoU (Fewer Overlaps)'},
            ]
            
            results = []
            
            for config in test_configs:
                print(f"\n📊 Testing: {config['name']}")
                print(f"   Confidence: {config['conf']}, IoU: {config['iou']}")
                
                # Create service with test parameters
                service = ComponentDetectionService(
                    model_path=model_path,
                    confidence_threshold=config['conf'],
                    iou_threshold=config['iou']
                )
                
                # Run detection
                import asyncio
                async def run_detection():
                    return await service.detect_components_async(temp_path)
                
                result = asyncio.run(run_detection())
                
                # Analyze results
                detections = result.detections
                print(f"   Total detections: {len(detections)}")
                
                # Count by class
                class_counts = {}
                for detection in detections:
                    class_name = detection.class_name
                    if class_name not in class_counts:
                        class_counts[class_name] = 0
                    class_counts[class_name] += 1
                
                for class_name, count in class_counts.items():
                    print(f"   - {class_name}: {count}")
                
                # Check for specific issues
                ctb_count = class_counts.get('Cable Termination Box', 0)
                tou_count = class_counts.get('Single Phase Tap-Off Unit', 0)
                
                print(f"   Expected CTB: 3, Found: {ctb_count}")
                print(f"   Expected TOU: 2, Found: {tou_count}")
                
                if ctb_count < 3:
                    print(f"   ⚠️ Missing Cable Termination Box detections!")
                if tou_count > 2:
                    print(f"   ⚠️ Possible false positive Single Phase Tap-Off Units!")
                
                results.append({
                    'config': config,
                    'total_detections': len(detections),
                    'class_counts': class_counts,
                    'ctb_found': ctb_count,
                    'tou_found': tou_count,
                    'processing_time': result.processing_time
                })
            
            # Analyze results
            print(f"\n📈 Analysis Summary:")
            print("=" * 60)
            
            best_ctb_config = max(results, key=lambda x: x['ctb_found'])
            least_tou_fp_config = min(results, key=lambda x: x['tou_found'])
            
            print(f"🎯 Best Cable Termination Box Detection:")
            print(f"   Config: {best_ctb_config['config']['name']}")
            print(f"   Found: {best_ctb_config['ctb_found']}/3 CTB")
            print(f"   Conf: {best_ctb_config['config']['conf']}, IoU: {best_ctb_config['config']['iou']}")
            
            print(f"\n🎯 Least Single Phase Tap-Off Unit False Positives:")
            print(f"   Config: {least_tou_fp_config['config']['name']}")
            print(f"   Found: {least_tou_fp_config['tou_found']} TOU (expected: 2)")
            print(f"   Conf: {least_tou_fp_config['config']['conf']}, IoU: {least_tou_fp_config['config']['iou']}")
            
            # Recommendations
            print(f"\n💡 Recommendations:")
            print("=" * 40)
            
            if best_ctb_config['ctb_found'] < 3:
                print(f"❌ Cable Termination Box Detection Issues:")
                print(f"   - Model may need retraining with more CTB examples")
                print(f"   - Try lower confidence threshold (current best: {best_ctb_config['config']['conf']})")
                print(f"   - Consider image preprocessing (contrast enhancement)")
            
            if least_tou_fp_config['tou_found'] > 2:
                print(f"❌ Single Phase Tap-Off Unit False Positives:")
                print(f"   - Model may be over-generalizing TOU features")
                print(f"   - Try higher confidence threshold")
                print(f"   - Consider stricter IoU threshold")
                print(f"   - May need negative examples in training data")
            
            # Optimal configuration suggestion
            optimal_configs = [r for r in results if r['ctb_found'] >= 2 and r['tou_found'] <= 3]
            if optimal_configs:
                best_overall = min(optimal_configs, key=lambda x: abs(x['tou_found'] - 2) + abs(x['ctb_found'] - 3))
                print(f"\n🏆 Recommended Configuration:")
                print(f"   Config: {best_overall['config']['name']}")
                print(f"   Confidence: {best_overall['config']['conf']}")
                print(f"   IoU: {best_overall['config']['iou']}")
                print(f"   CTB Found: {best_overall['ctb_found']}/3")
                print(f"   TOU Found: {best_overall['tou_found']}/2")
            
            return results
            
        finally:
            os.unlink(temp_path)
        
    except Exception as e:
        print(f"❌ Detection testing failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🚀 YOLO Detection Accuracy Analysis")
    print("=" * 60)

    # Run analysis
    analyze_detection_parameters()
    results = test_detection_with_different_parameters()

    if results:
        print(f"\n✅ Analysis complete! Check recommendations above.")
    else:
        print(f"\n❌ Analysis failed. Check error messages above.")
