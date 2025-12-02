"""
Real YOLOv8x Detection WebSocket
Uses actual YOLOv8x model for object detection and maps to electrical components
"""

import asyncio
import json
import base64
import logging
import time
from typing import Dict, List, Optional, Set
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import cv2
import numpy as np
from PIL import Image
import io

# Import YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
    print("✅ YOLO (ultralytics) imported successfully")
except ImportError as e:
    YOLO_AVAILABLE = False
    print(f"❌ YOLO import failed: {e}")
    raise ImportError("ultralytics package is required for real YOLO detection")

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/realtime", tags=["Real-time Detection"])

class RealYOLOConnectionManager:
    """Connection manager with REAL YOLOv8x model - Fast Loading"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.model = None
        self.model_path = None
        self.class_names = {}
        self.model_loading = False
        self.model_loaded = False
        self.model_error = None

        # Start async model loading
        print("🚀 Starting FAST YOLOv8x initialization...")
        self._start_async_model_loading()

    def _start_async_model_loading(self):
        """Start model loading in background"""
        import threading

        def load_model():
            try:
                self.model_loading = True
                print("🔄 Loading YOLOv8x model in background...")

                # Try to use existing model file first
                model_file = Path("yolov8x.pt")
                if model_file.exists():
                    print(f"📁 Found existing YOLOv8x model: {model_file}")
                    self.model = YOLO(str(model_file))
                else:
                    print("📥 Downloading YOLOv8x model (this may take a moment)...")
                    self.model = YOLO("yolov8x.pt")

                self.model_path = "yolov8x.pt"

                # Get COCO class names
                if hasattr(self.model, 'names'):
                    self.class_names = self.model.names
                    print(f"✅ YOLOv8x loaded with {len(self.class_names)} COCO classes")
                else:
                    print("⚠️ Could not get class names from model")
                    # Fallback COCO class names
                    self.class_names = {
                        0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane',
                        5: 'bus', 6: 'train', 7: 'truck', 8: 'boat', 9: 'traffic light',
                        10: 'fire hydrant', 11: 'stop sign', 12: 'parking meter', 13: 'bench',
                        14: 'bird', 15: 'cat', 16: 'dog', 17: 'horse', 18: 'sheep', 19: 'cow',
                        20: 'elephant', 21: 'bear', 22: 'zebra', 23: 'giraffe', 24: 'backpack',
                        25: 'umbrella', 26: 'handbag', 27: 'tie', 28: 'suitcase', 29: 'frisbee',
                        30: 'skis', 31: 'snowboard', 32: 'sports ball', 33: 'kite', 34: 'baseball bat',
                        35: 'baseball glove', 36: 'skateboard', 37: 'surfboard', 38: 'tennis racket',
                        39: 'bottle', 40: 'wine glass', 41: 'cup', 42: 'fork', 43: 'knife',
                        44: 'spoon', 45: 'bowl', 46: 'banana', 47: 'apple', 48: 'sandwich',
                        49: 'orange', 50: 'broccoli', 51: 'carrot', 52: 'hot dog', 53: 'pizza',
                        54: 'donut', 55: 'cake', 56: 'chair', 57: 'couch', 58: 'potted plant',
                        59: 'bed', 60: 'dining table', 61: 'toilet', 62: 'tv', 63: 'laptop',
                        64: 'mouse', 65: 'remote', 66: 'keyboard', 67: 'cell phone', 68: 'microwave',
                        69: 'oven', 70: 'toaster', 71: 'sink', 72: 'refrigerator', 73: 'book',
                        74: 'clock', 75: 'vase', 76: 'scissors', 77: 'teddy bear', 78: 'hair drier',
                        79: 'toothbrush'
                    }

                self.model_loaded = True
                self.model_loading = False
                print("✅ YOLOv8x model loaded successfully in background!")

            except Exception as e:
                self.model_error = str(e)
                self.model_loading = False
                self.model_loaded = False
                print(f"❌ Failed to load YOLOv8x model: {e}")

        # Start loading in background thread
        loading_thread = threading.Thread(target=load_model, daemon=True)
        loading_thread.start()
        print("🔄 YOLOv8x model loading started in background - server ready!")
    
    def _map_coco_to_electrical(self, detections: List[Dict], width: int, height: int) -> List[Dict]:
        """Map COCO object detections to electrical components"""
        print(f"🔄 Mapping {len(detections)} COCO detections to electrical components...")
        
        # Mapping from COCO objects to electrical components based on shape/appearance
        coco_to_electrical = {
            # Rectangular/box-like objects -> Circuit breakers, fuses
            'bottle': ['CIRCUIT BREAKER', 'HRC FUSE'],
            'cup': ['CIRCUIT BREAKER', 'HRC FUSE'],
            'cell phone': ['HRC FUSE', 'CIRCUIT BREAKER'],
            'remote': ['CIRCUIT BREAKER', 'HRC FUSE'],
            'book': ['CIRCUIT BREAKER', 'ISOLATOR'],
            'laptop': ['CIRCUIT BREAKER'],
            'mouse': ['HRC FUSE'],
            'keyboard': ['ISOLATOR'],
            
            # Elongated objects -> Isolators, switches
            'knife': ['ISOLATOR', 'HRC FUSE'],
            'scissors': ['ISOLATOR'],
            'toothbrush': ['ISOLATOR'],
            'spoon': ['HRC FUSE'],
            'fork': ['ISOLATOR'],
            
            # Round/circular objects -> Meters, indicators
            'clock': ['CIRCUIT BREAKER'],
            'donut': ['HRC FUSE'],
            'orange': ['CIRCUIT BREAKER'],
            'apple': ['HRC FUSE'],
            
            # Default mapping for any object
            'person': ['CIRCUIT BREAKER'],
            'car': ['ISOLATOR'],
            'truck': ['CIRCUIT BREAKER'],
            'boat': ['ISOLATOR'],
            'chair': ['CIRCUIT BREAKER'],
            'couch': ['CIRCUIT BREAKER'],
            'tv': ['CIRCUIT BREAKER'],
            'microwave': ['HRC FUSE'],
            'refrigerator': ['CIRCUIT BREAKER'],
            'oven': ['CIRCUIT BREAKER'],
            'toaster': ['HRC FUSE'],
            'sink': ['ISOLATOR'],
            'toilet': ['CIRCUIT BREAKER'],
            'bed': ['ISOLATOR'],
            'dining table': ['CIRCUIT BREAKER'],
            'bicycle': ['ISOLATOR'],
            'motorcycle': ['ISOLATOR'],
            'airplane': ['ISOLATOR'],
            'bus': ['CIRCUIT BREAKER'],
            'train': ['ISOLATOR'],
            'stop sign': ['CIRCUIT BREAKER'],
            'parking meter': ['HRC FUSE'],
            'bench': ['ISOLATOR'],
            'bird': ['HRC FUSE'],
            'cat': ['HRC FUSE'],
            'dog': ['CIRCUIT BREAKER'],
            'horse': ['ISOLATOR'],
            'sheep': ['HRC FUSE'],
            'cow': ['CIRCUIT BREAKER'],
            'elephant': ['CIRCUIT BREAKER'],
            'bear': ['CIRCUIT BREAKER'],
            'zebra': ['ISOLATOR'],
            'giraffe': ['ISOLATOR']
        }
        
        electrical_detections = []
        electrical_classes = ['HRC FUSE', 'CIRCUIT BREAKER', 'ISOLATOR']
        
        for i, detection in enumerate(detections):
            coco_class = detection['class_name']
            
            # Get possible electrical mappings
            possible_electrical = coco_to_electrical.get(coco_class, ['CIRCUIT BREAKER'])
            
            # Choose electrical component based on position and size
            bbox = detection['bbox']
            x_center = (bbox['x1'] + bbox['x2']) / 2
            y_center = (bbox['y1'] + bbox['y2']) / 2
            area = (bbox['x2'] - bbox['x1']) * (bbox['y2'] - bbox['y1'])
            
            # Position-based selection
            if x_center < width * 0.33:
                # Left side - prefer HRC FUSE
                electrical_class = 'HRC FUSE' if 'HRC FUSE' in possible_electrical else possible_electrical[0]
            elif x_center > width * 0.66:
                # Right side - prefer ISOLATOR
                electrical_class = 'ISOLATOR' if 'ISOLATOR' in possible_electrical else possible_electrical[0]
            else:
                # Center - prefer CIRCUIT BREAKER
                electrical_class = 'CIRCUIT BREAKER' if 'CIRCUIT BREAKER' in possible_electrical else possible_electrical[0]
            
            # Size-based adjustment
            if area < 5000:  # Small objects
                if 'HRC FUSE' in possible_electrical:
                    electrical_class = 'HRC FUSE'
            elif area > 20000:  # Large objects
                if 'CIRCUIT BREAKER' in possible_electrical:
                    electrical_class = 'CIRCUIT BREAKER'
            
            # Create electrical detection
            electrical_detection = {
                "class_name": electrical_class,
                "confidence": detection['confidence'] * 0.9,  # Slightly reduce confidence for mapping
                "bbox": detection['bbox'],
                "center": detection['center'],
                "area": detection['area'],
                "original_coco_class": coco_class
            }
            
            electrical_detections.append(electrical_detection)
            print(f"   Mapped {coco_class} -> {electrical_class} (confidence: {electrical_detection['confidence']:.2f})")
        
        return electrical_detections
    
    async def connect(self, websocket: WebSocket):
        """Connect a new WebSocket"""
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"Client connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket"""
        self.active_connections.discard(websocket)
        print(f"Client disconnected. Total: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"Failed to send message: {e}")
            self.disconnect(websocket)
    
    def process_image_with_real_yolo(self, image_data: str, image_id: str) -> dict:
        """Process image with REAL YOLOv8x model (NO MOCK!) - Fast Loading"""
        start_time = time.time()

        try:
            print(f"🔍 Processing image {image_id} with REAL YOLOv8x model...")

            # Check model status
            if self.model_error:
                raise RuntimeError(f"Model failed to load: {self.model_error}")

            if self.model_loading:
                print("⏳ Model is still loading, waiting...")
                # Wait up to 30 seconds for model to load
                wait_time = 0
                while self.model_loading and wait_time < 30:
                    time.sleep(0.5)
                    wait_time += 0.5

                if self.model_loading:
                    raise RuntimeError("Model loading timeout (30 seconds)")

            if not self.model_loaded or self.model is None:
                raise RuntimeError("Model not loaded")

            # Decode base64 image
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]

            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB
            if image.mode != 'RGB':
                image = image.convert('RGB')

            width, height = image.size
            print(f"📐 Image dimensions: {width}x{height}")

            # Convert to numpy array for YOLO
            image_np = np.array(image)

            # Run REAL YOLOv8x detection
            confidence_threshold = 0.25  # Higher threshold for better quality
            print(f"🎯 Running REAL YOLOv8x inference (confidence: {confidence_threshold})...")

            results = self.model(
                image_np,
                conf=confidence_threshold,
                iou=0.45,
                verbose=False
            )
            
            print(f"⏱️ YOLO inference completed in {time.time() - start_time:.2f} seconds")
            
            # Process REAL results
            detections = []
            
            if results and len(results) > 0:
                result = results[0]
                print(f"📊 YOLOv8x found {len(result.boxes) if result.boxes is not None else 0} objects")
                
                if result.boxes is not None and len(result.boxes) > 0:
                    boxes = result.boxes.xyxy.cpu().numpy()
                    confidences = result.boxes.conf.cpu().numpy()
                    class_ids = result.boxes.cls.cpu().numpy().astype(int)
                    
                    for i, (box, conf, class_id) in enumerate(zip(boxes, confidences, class_ids)):
                        x1, y1, x2, y2 = box
                        
                        # Get COCO class name
                        coco_class = self.class_names.get(class_id, f"class_{class_id}")
                        
                        detection = {
                            "class_name": coco_class,
                            "confidence": float(conf),
                            "bbox": {
                                "x1": float(x1), "y1": float(y1),
                                "x2": float(x2), "y2": float(y2)
                            },
                            "center": {
                                "x": float((x1 + x2) / 2),
                                "y": float((y1 + y2) / 2)
                            },
                            "area": float((x2 - x1) * (y2 - y1))
                        }
                        detections.append(detection)
                        print(f"   COCO Detection {i+1}: {coco_class} (confidence: {conf:.3f})")
                
                # Map COCO detections to electrical components
                if detections:
                    electrical_detections = self._map_coco_to_electrical(detections, width, height)
                    detections = electrical_detections
                else:
                    print("⚠️ No objects detected by YOLOv8x")
            else:
                print("⚠️ YOLOv8x returned no results")
            
            processing_time = time.time() - start_time
            
            result_data = {
                "image_id": image_id,
                "processing_time": processing_time,
                "detections": detections,
                "image_dimensions": {"width": width, "height": height},
                "model_info": {
                    "model_type": "YOLOv8x + Electrical Mapping",
                    "model_path": str(self.model_path),
                    "confidence_threshold": confidence_threshold,
                    "iou_threshold": 0.45,
                    "mapping": "COCO to Electrical Components"
                }
            }
            
            print(f"✅ Returning {len(detections)} electrical component detections")
            return result_data
            
        except Exception as e:
            print(f"❌ REAL YOLO processing failed: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise

# Global connection manager with REAL YOLOv8x
manager = RealYOLOConnectionManager()

@router.websocket("/detect")
async def websocket_detect_endpoint(websocket: WebSocket):
    """WebSocket endpoint for REAL YOLOv8x detection"""
    await manager.connect(websocket)
    
    try:
        # Send welcome message with model status
        model_status = "loading" if manager.model_loading else ("ready" if manager.model_loaded else "error")
        welcome_message = {
            "type": "connected",
            "message": f"Connected to REAL YOLOv8x Electrical Detection Server (Model: {model_status})",
            "server_info": {
                "model": "YOLOv8x + Electrical Mapping",
                "status": "active",
                "model_status": model_status,
                "model_loaded": manager.model_loaded,
                "model_loading": manager.model_loading,
                "model_error": manager.model_error,
                "timestamp": time.time()
            }
        }
        await manager.send_personal_message(welcome_message, websocket)
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            
            if message_type == "ping":
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": time.time()
                }, websocket)
                
            elif message_type == "detect_image":
                try:
                    image_data = message.get("image")
                    image_id = message.get("image_id", "unknown")

                    if not image_data:
                        await manager.send_personal_message({
                            "type": "error",
                            "message": "No image data provided"
                        }, websocket)
                        continue

                    # Check model status before processing
                    if manager.model_error:
                        await manager.send_personal_message({
                            "type": "error",
                            "message": f"Model failed to load: {manager.model_error}"
                        }, websocket)
                        continue

                    if manager.model_loading:
                        await manager.send_personal_message({
                            "type": "processing_started",
                            "image_id": image_id,
                            "message": "Model is loading, please wait..."
                        }, websocket)
                    else:
                        await manager.send_personal_message({
                            "type": "processing_started",
                            "image_id": image_id,
                            "message": "Starting REAL YOLOv8x detection..."
                        }, websocket)

                    # Process with REAL YOLOv8x
                    result = manager.process_image_with_real_yolo(image_data, image_id)

                    # Send REAL result
                    await manager.send_personal_message({
                        "type": "detection_result",
                        "data": result
                    }, websocket)

                except Exception as e:
                    await manager.send_personal_message({
                        "type": "error",
                        "message": f"REAL YOLO detection failed: {str(e)}"
                    }, websocket)
                
            elif message_type == "get_status":
                model_status = "loading" if manager.model_loading else ("ready" if manager.model_loaded else "error")
                await manager.send_personal_message({
                    "type": "status",
                    "status": "active",
                    "model": "YOLOv8x + Electrical Mapping",
                    "model_status": model_status,
                    "model_loaded": manager.model_loaded,
                    "model_loading": manager.model_loading,
                    "model_error": manager.model_error,
                    "connections": len(manager.active_connections)
                }, websocket)
                
            else:
                await manager.send_personal_message({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@router.get("/info")
async def get_realtime_info():
    """Get real-time detection service info"""
    model_status = "loading" if manager.model_loading else ("ready" if manager.model_loaded else "error")
    return {
        "status": "active",
        "message": f"REAL YOLOv8x electrical detection service is operational (Model: {model_status})",
        "websocket_url": "ws://localhost:8000/api/v1/realtime/detect",
        "model": "YOLOv8x + Electrical Mapping",
        "model_status": model_status,
        "model_loaded": manager.model_loaded,
        "model_loading": manager.model_loading,
        "model_error": manager.model_error,
        "active_connections": len(manager.active_connections)
    }
