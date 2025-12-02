"""
Real-time Component Detection WebSocket API
Provides WebSocket endpoints for real-time YOLO component detection
"""

import asyncio
import json
import base64
import logging
import time
from typing import Dict, List, Optional, Set
from pathlib import Path
import traceback

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse
import cv2
import numpy as np
from PIL import Image
import io

from services.component_service import ComponentDetectionService, get_component_service
from utils.logging_config import StructuredLogger

# Configure logging
logger = logging.getLogger(__name__)
structured_logger = StructuredLogger()

# Create router
router = APIRouter(prefix="/api/v1/realtime", tags=["Real-time Detection"])

class ConnectionManager:
    """Manages WebSocket connections for real-time detection with stability features"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_info: Dict[WebSocket, Dict] = {}
        self.heartbeat_task = None
        self.heartbeat_interval = 30  # seconds
    
    async def connect(self, websocket: WebSocket, client_info: Dict = None):
        """Accept a new WebSocket connection with heartbeat setup"""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_info[websocket] = {
            **(client_info or {}),
            "connected_at": time.time(),
            "last_activity": time.time()
        }
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

        # Start heartbeat if first connection
        if len(self.active_connections) == 1:
            self.start_heartbeat()

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection with cleanup"""
        self.active_connections.discard(websocket)
        self.connection_info.pop(websocket, None)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

        # Stop heartbeat if no connections
        if len(self.active_connections) == 0:
            self.stop_heartbeat()
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific client"""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message, default=str))
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    def start_heartbeat(self):
        """Start heartbeat task to maintain connections"""
        if not self.heartbeat_task:
            self.heartbeat_task = asyncio.create_task(self.heartbeat_loop())
            logger.info("Started WebSocket heartbeat")

    def stop_heartbeat(self):
        """Stop heartbeat task"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            self.heartbeat_task = None
            logger.info("Stopped WebSocket heartbeat")

    async def heartbeat_loop(self):
        """Heartbeat loop to maintain connections"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                # Send heartbeat to all active connections
                dead_connections = []

                for websocket in list(self.active_connections):
                    try:
                        await websocket.send_text(json.dumps({
                            "type": "heartbeat",
                            "timestamp": time.time()
                        }))
                    except Exception:
                        dead_connections.append(websocket)

                # Remove dead connections
                for websocket in dead_connections:
                    self.disconnect(websocket)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

# Global connection manager
manager = ConnectionManager()

class RealtimeDetectionHandler:
    """Handles real-time detection requests"""
    
    def __init__(self, component_service: ComponentDetectionService):
        self.component_service = component_service
    
    def decode_base64_image(self, base64_string: str) -> np.ndarray:
        """
        Decode base64 image string to numpy array
        
        Args:
            base64_string: Base64 encoded image
            
        Returns:
            Image as numpy array (BGR format)
        """
        try:
            # Remove data URL prefix if present
            if base64_string.startswith('data:image'):
                base64_string = base64_string.split(',')[1]
            
            # Decode base64
            image_data = base64.b64decode(base64_string)
            
            # Convert to PIL Image
            pil_image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Convert to numpy array (RGB)
            image_array = np.array(pil_image)
            
            # Convert RGB to BGR for OpenCV
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            return image_bgr
            
        except Exception as e:
            logger.error(f"Failed to decode base64 image: {e}")
            raise
    
    async def process_detection_request(self, websocket: WebSocket, message_data: dict):
        """
        Process a detection request from WebSocket client with enhanced error handling

        Args:
            websocket: Client WebSocket connection
            message_data: Request data containing image and parameters
        """
        temp_path = None

        try:
            # Extract and validate request data
            image_base64 = message_data.get("image")
            image_id = message_data.get("image_id", f"realtime_{int(time.time() * 1000)}")
            confidence_threshold = float(message_data.get("confidence_threshold", 0.03))
            iou_threshold = float(message_data.get("iou_threshold", 0.45))

            if not image_base64:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "No image data provided"
                }, websocket)
                return

            # Send processing started message
            await manager.send_personal_message({
                "type": "processing_started",
                "image_id": image_id,
                "message": "Starting YOLOv8x detection..."
            }, websocket)

            # Validate image size (max 10MB base64)
            if len(image_base64) > 10 * 1024 * 1024:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Image too large (max 10MB)"
                }, websocket)
                return

            # Decode image with enhanced error handling
            logger.info(f"Processing real-time detection request: {image_id}")
            try:
                image = self.decode_base64_image(image_base64)

                # Validate image dimensions
                height, width = image.shape[:2]
                if width > 4096 or height > 4096:
                    await manager.send_personal_message({
                        "type": "error",
                        "message": f"Image too large: {width}x{height} (max 4096x4096)"
                    }, websocket)
                    return

                # Resize if needed for faster processing
                if max(width, height) > 1280:
                    scale = 1280 / max(width, height)
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
                    logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")

            except Exception as e:
                await manager.send_personal_message({
                    "type": "error",
                    "message": f"Failed to decode image: {str(e)}"
                }, websocket)
                return

            # Save temporary image file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                cv2.imwrite(tmp_file.name, image)
                temp_path = Path(tmp_file.name)

            try:
                # Update service parameters
                self.component_service.confidence_threshold = confidence_threshold
                self.component_service.iou_threshold = iou_threshold

                # Send progress update
                await manager.send_personal_message({
                    "type": "processing_progress",
                    "image_id": image_id,
                    "message": "Running YOLOv8x inference..."
                }, websocket)

                # Run detection with timeout (30 seconds max)
                start_time = time.time()
                try:
                    result = await asyncio.wait_for(
                        self.component_service.detect_components_async(
                            image_path=temp_path,
                            save_visualization=False
                        ),
                        timeout=30.0
                    )
                except asyncio.TimeoutError:
                    await manager.send_personal_message({
                        "type": "error",
                        "message": "Processing timeout (30s limit exceeded)"
                    }, websocket)
                    return

                processing_time = time.time() - start_time
                
                # Format response
                response = {
                    "type": "detection_result",
                    "data": {
                        "image_id": image_id,
                        "processing_time": processing_time,
                        "detections": [
                            {
                                "class_name": detection.class_name,
                                "confidence": detection.confidence,
                                "bbox": {
                                    "x1": detection.bbox[0],
                                    "y1": detection.bbox[1],
                                    "x2": detection.bbox[2],
                                    "y2": detection.bbox[3]
                                },
                                "center": {
                                    "x": detection.center[0],
                                    "y": detection.center[1]
                                },
                                "area": detection.area
                            }
                            for detection in result.detections
                        ],
                        "image_dimensions": {
                            "width": result.image_dimensions[0],
                            "height": result.image_dimensions[1]
                        },
                        "model_info": {
                            "model_type": "YOLOv8x",
                            "confidence_threshold": str(confidence_threshold),
                            "iou_threshold": str(iou_threshold)
                        }
                    }
                }
                
                # Send response
                await manager.send_personal_message(response, websocket)
                
                # Log detection
                structured_logger.log_component_detection(
                    image_path=image_id,
                    detections_count=len(result.detections),
                    processing_time=processing_time,
                    model_info=f"Real-time YOLOv8x (conf={confidence_threshold})"
                )
                
                logger.info(f"✅ Real-time detection completed: {len(result.detections)} components found in {processing_time:.3f}s")
                
            finally:
                # Clean up temporary file
                try:
                    if temp_path and temp_path.exists():
                        temp_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Real-time detection failed: {e}")
            logger.error(traceback.format_exc())
            
            await manager.send_personal_message({
                "type": "error",
                "message": f"Detection failed: {str(e)}"
            }, websocket)
    
    async def handle_ping(self, websocket: WebSocket):
        """Handle ping request"""
        await manager.send_personal_message({
            "type": "pong",
            "timestamp": time.time()
        }, websocket)
    
    async def send_welcome_message(self, websocket: WebSocket):
        """Send welcome message with server info"""
        welcome_message = {
            "type": "connected",
            "message": "Connected to SLD real-time detection server",
            "server_info": {
                "model_type": "YOLOv8x",
                "confidence_threshold": self.component_service.confidence_threshold,
                "iou_threshold": self.component_service.iou_threshold,
                "supported_classes": list(self.component_service._detector.class_names.values()) if self.component_service._detector else [],
                "version": "1.0.0"
            }
        }
        await manager.send_personal_message(welcome_message, websocket)

# WebSocket endpoint
@router.websocket("/detect")
async def websocket_detect_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time component detection
    Fixed version without dependency injection issues

    Accepts WebSocket connections and processes real-time detection requests.

    Message format:
    {
        "type": "detect_image",
        "image": "base64_encoded_image",
        "image_id": "optional_image_id",
        "confidence_threshold": 0.03,
        "iou_threshold": 0.45
    }
    """
    # Create component service instance
    try:
        component_service = get_component_service()
    except Exception as e:
        logger.error(f"Failed to initialize component service: {e}")
        await websocket.close(code=1011, reason="Service initialization failed")
        return

    # Create detection handler
    handler = RealtimeDetectionHandler(component_service)

    # Accept connection
    await manager.connect(websocket)

    try:
        # Send welcome message
        await handler.send_welcome_message(websocket)

        # Listen for messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                message_type = message.get("type")

                if message_type == "detect_image":
                    await handler.process_detection_request(websocket, message)

                elif message_type == "ping":
                    await handler.handle_ping(websocket)

                elif message_type == "get_status":
                    # Send server status
                    status_message = {
                        "type": "status",
                        "data": {
                            "connected_clients": len(manager.active_connections),
                            "server_time": time.time(),
                            "model_loaded": component_service._detector is not None,
                            "model_info": {
                                "confidence_threshold": component_service.confidence_threshold,
                                "iou_threshold": component_service.iou_threshold
                            }
                        }
                    }
                    await manager.send_personal_message(status_message, websocket)

                else:
                    # Unknown message type
                    await manager.send_personal_message({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    }, websocket)

            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON message format"
                }, websocket)

            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await manager.send_personal_message({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                }, websocket)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)

# REST endpoint for WebSocket info
@router.get("/info")
async def get_realtime_info():
    """
    Get information about the real-time detection service

    Returns:
        Service information including connection count and capabilities
    """
    return JSONResponse({
        "service": "Real-time Component Detection",
        "version": "1.0.0",
        "websocket_endpoint": "/api/v1/realtime/detect",
        "connected_clients": len(manager.active_connections),
        "capabilities": {
            "real_time_detection": True,
            "batch_processing": False,
            "supported_formats": ["image/jpeg", "image/png", "image/bmp"],
            "max_image_size": "10MB",
            "supported_classes": 23
        },
        "message_types": {
            "detect_image": "Send image for detection",
            "ping": "Test connection",
            "get_status": "Get server status"
        }
    })

# Health check endpoint
@router.get("/health")
async def realtime_health_check(
    component_service: ComponentDetectionService = Depends(get_component_service)
):
    """
    Health check for real-time detection service

    Returns:
        Health status and service information
    """
    try:
        # Check if model is loaded
        model_loaded = component_service._detector is not None

        # Check WebSocket connections
        active_connections = len(manager.active_connections)

        health_status = {
            "status": "healthy" if model_loaded else "degraded",
            "timestamp": time.time(),
            "checks": {
                "model_loaded": model_loaded,
                "websocket_manager": True,
                "active_connections": active_connections
            },
            "service_info": {
                "model_type": "YOLOv8x",
                "confidence_threshold": component_service.confidence_threshold,
                "iou_threshold": component_service.iou_threshold
            }
        }

        return JSONResponse(health_status)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse({
            "status": "unhealthy",
            "timestamp": time.time(),
            "error": str(e)
        }, status_code=503)
