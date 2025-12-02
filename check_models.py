"""Quick script to check model classes"""
from ultralytics import YOLO
import sys

models_to_check = [
    "C:/Users/admin/Downloads/SLD/YOLO/sld_yolov8_project/models/trained_models/best.pt",
    "C:/Users/admin/Downloads/SLD/SLD-New/YOLO/runs/detect/unified_model/weights/best.pt",
    "C:/Users/admin/Downloads/SLD/SLD-New/YOLO/runs/detect/unified_model2/weights/best.pt",
    "C:/Users/admin/Downloads/SLD/SLD-New/YOLO-Reorganized/training/models/cb3_trained_best.pt",
    "C:/Users/admin/Downloads/SLD/SLD-YOLO/runs/detect/circuit_breaker_model5/weights/best.pt",
]

print("Checking models for class counts...\n")

for model_path in models_to_check:
    try:
        model = YOLO(model_path)
        print(f"✅ {model_path.split('/')[-3:]}")
        print(f"   Classes: {len(model.names)}")
        print(f"   Names: {model.names}")
        print()
    except Exception as e:
        print(f"❌ {model_path}: {e}\n")
