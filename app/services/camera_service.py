import asyncio
import cv2
import numpy as np
import logging
import json
import base64
from typing import Dict, List, Optional
from datetime import datetime
import threading
import time

from app.services.face_recognition_service import FaceRecognitionService
from app.core.config import settings

logger = logging.getLogger(__name__)

class CameraService:
    """Service for camera operations and video processing"""
    
    def __init__(self):
        self.is_active = False
        self.camera = None
        self.face_service = None
        self.latest_frame = None
        self.latest_events = []
        self.processing_thread = None
        self.stop_event = threading.Event()
        self.frame_lock = threading.Lock()
        self.events_lock = threading.Lock()
        
        # Statistics
        self.fps = 0
        self.detected_faces = 0
        self.recognized_faces = 0
        self.last_recognition = None
        
        # Configuration
        self.config = {
            "camera_id": 0,
            "resolution": (640, 480),
            "fps_target": 30,
            "detection_threshold": settings.FACE_DETECTION_THRESHOLD,
            "recognition_threshold": settings.FACE_RECOGNITION_THRESHOLD
        }
    
    async def get_status(self) -> Dict:
        """Get camera system status"""
        return {
            "active": self.is_active,
            "fps": self.fps,
            "detected_faces": self.detected_faces,
            "recognized_faces": self.recognized_faces,
            "last_recognition": self.last_recognition,
            "camera_connected": self.camera is not None and self.camera.isOpened() if self.camera else False
        }
    
    async def start_processing(self) -> Dict:
        """Start camera processing"""
        if self.is_active:
            return {"success": True, "message": "Camera already active"}
        
        try:
            # Initialize face recognition service
            if not self.face_service:
                self.face_service = FaceRecognitionService()
                await self.face_service.initialize()
            
            # Initialize camera
            self.camera = cv2.VideoCapture(self.config["camera_id"])
            if not self.camera.isOpened():
                return {"success": False, "error": "Failed to open camera"}
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.config["resolution"][0])
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config["resolution"][1])
            self.camera.set(cv2.CAP_PROP_FPS, self.config["fps_target"])
            
            # Start processing thread
            self.stop_event.clear()
            self.processing_thread = threading.Thread(target=self._processing_loop)
            self.processing_thread.daemon = True
            self.processing_thread.start()
            
            self.is_active = True
            logger.info("Camera processing started successfully")
            
            return {"success": True, "message": "Camera processing started"}
            
        except Exception as e:
            logger.error(f"Error starting camera processing: {e}")
            return {"success": False, "error": str(e)}
    
    async def stop_processing(self) -> Dict:
        """Stop camera processing"""
        if not self.is_active:
            return {"success": True, "message": "Camera already inactive"}
        
        try:
            # Signal stop
            self.stop_event.set()
            self.is_active = False
            
            # Wait for processing thread to finish
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=5)
            
            # Release camera
            if self.camera:
                self.camera.release()
                self.camera = None
            
            logger.info("Camera processing stopped successfully")
            return {"success": True, "message": "Camera processing stopped"}
            
        except Exception as e:
            logger.error(f"Error stopping camera processing: {e}")
            return {"success": False, "error": str(e)}
    
    def _processing_loop(self):
        """Main processing loop for camera frames"""
        frame_count = 0
        start_time = time.time()
        
        try:
            # Initialize face detection (using InsightFace)
            from insightface.app import FaceAnalysis
            face_app = FaceAnalysis(name='antelopev2')
            face_app.prepare(ctx_id=0, det_size=(416, 416))
            
            while not self.stop_event.is_set() and self.camera and self.camera.isOpened():
                ret, frame = self.camera.read()
                if not ret:
                    logger.warning("Failed to read frame from camera")
                    continue
                
                frame_count += 1
                
                # Calculate FPS
                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    self.fps = frame_count / elapsed if elapsed > 0 else 0
                
                # Process frame for face detection and recognition
                processed_frame, detections = self._process_frame(frame, face_app)
                
                # Update latest frame
                with self.frame_lock:
                    # Convert frame to base64 for web transmission
                    _, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    frame_b64 = base64.b64encode(buffer).decode('utf-8')
                    
                    self.latest_frame = {
                        "frame": frame_b64,
                        "detections": detections,
                        "timestamp": datetime.now().isoformat()
                    }
                
                # Small delay to control frame rate
                time.sleep(1 / self.config["fps_target"])
                
        except Exception as e:
            logger.error(f"Error in camera processing loop: {e}")
        finally:
            logger.info("Camera processing loop ended")
    
    def _process_frame(self, frame: np.ndarray, face_app) -> tuple:
        """Process a single frame for face detection and recognition"""
        detections = []
        processed_frame = frame.copy()
        
        try:
            # Detect faces
            faces = face_app.get(frame)
            self.detected_faces = len(faces)
            
            for face in faces:
                # Get bounding box
                bbox = face.bbox.astype(int)
                x1, y1, x2, y2 = bbox
                
                # Draw bounding box
                cv2.rectangle(processed_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Perform recognition
                recognition_result = None
                if self.face_service:
                    # This would be async in real implementation, but for demo we'll make it sync
                    try:
                        # Create a simple sync version for the processing loop
                        recognition_result = self._sync_recognize_face(face.embedding)
                    except Exception as e:
                        logger.error(f"Error in face recognition: {e}")
                
                detection_info = {
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "confidence": float(face.det_score),
                    "recognition": recognition_result
                }
                
                # Draw recognition result
                if recognition_result:
                    label = f"{recognition_result['employee_name']} ({recognition_result['confidence']:.2f})"
                    cv2.putText(processed_frame, label, (x1, y1-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                    # Log recognition event
                    self._log_recognition_event(recognition_result)
                    self.recognized_faces += 1
                else:
                    cv2.putText(processed_frame, "Unknown", (x1, y1-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                
                detections.append(detection_info)
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
        
        return processed_frame, detections
    
    def _sync_recognize_face(self, face_embedding: np.ndarray) -> Optional[Dict]:
        """Synchronous version of face recognition for processing loop"""
        if not self.face_service or not self.face_service.embeddings:
            return None
        
        try:
            # Calculate similarities
            similarities = []
            for known_embedding in self.face_service.embeddings:
                similarity = self.face_service._calculate_similarity(face_embedding, known_embedding)
                similarities.append(similarity)
            
            if not similarities:
                return None
            
            # Find best match
            max_similarity = max(similarities)
            best_match_idx = similarities.index(max_similarity)
            
            if max_similarity >= self.face_service.recognition_threshold:
                employee_id = self.face_service.labels[best_match_idx]
                
                # Get employee details from cache or database
                return {
                    "employee_id": employee_id,
                    "employee_name": f"Employee {employee_id}",  # Simplified for demo
                    "confidence": float(max_similarity)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in sync face recognition: {e}")
            return None
    
    def _log_recognition_event(self, recognition_result: Dict):
        """Log a recognition event"""
        try:
            event = {
                "employee_id": recognition_result["employee_id"],
                "employee_name": recognition_result["employee_name"],
                "confidence": recognition_result["confidence"],
                "timestamp": datetime.now().isoformat(),
                "camera_id": self.config["camera_id"],
                "event_type": "recognition"
            }
            
            with self.events_lock:
                self.latest_events.append(event)
                # Keep only last 100 events
                if len(self.latest_events) > 100:
                    self.latest_events = self.latest_events[-100:]
            
            self.last_recognition = event["timestamp"]
            
            # Here you would also log to database via face_service
            # asyncio.create_task(self.face_service.log_attendance(...))
            
        except Exception as e:
            logger.error(f"Error logging recognition event: {e}")
    
    async def get_latest_frame(self) -> Optional[Dict]:
        """Get the latest processed frame"""
        with self.frame_lock:
            return self.latest_frame.copy() if self.latest_frame else None
    
    async def get_latest_events(self) -> List[Dict]:
        """Get latest recognition events"""
        with self.events_lock:
            # Return new events and clear the list
            events = self.latest_events.copy()
            self.latest_events.clear()
            return events
    
    async def get_config(self) -> Dict:
        """Get camera configuration"""
        return self.config.copy()
    
    async def update_config(self, new_config: Dict) -> Dict:
        """Update camera configuration"""
        try:
            # Validate configuration
            valid_keys = ["camera_id", "resolution", "fps_target", "detection_threshold", "recognition_threshold"]
            
            for key, value in new_config.items():
                if key in valid_keys:
                    self.config[key] = value
            
            # If camera is active, restart with new config
            if self.is_active:
                await self.stop_processing()
                await self.start_processing()
            
            return {"success": True, "message": "Configuration updated"}
            
        except Exception as e:
            logger.error(f"Error updating camera config: {e}")
            return {"success": False, "error": str(e)}