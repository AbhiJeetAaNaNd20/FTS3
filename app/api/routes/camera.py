from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import asyncio
import json
import logging
from typing import List

from app.core.database import get_db
from app.models.user import User
from app.api.dependencies import require_camera_access
from app.services.camera_service import CameraService

router = APIRouter()
logger = logging.getLogger(__name__)

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

@router.get("/status")
async def get_camera_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_camera_access)
):
    """Get camera system status"""
    camera_service = CameraService()
    status = await camera_service.get_status()
    
    return {
        "camera_active": status.get("active", False),
        "processing_fps": status.get("fps", 0),
        "detected_faces": status.get("detected_faces", 0),
        "recognized_faces": status.get("recognized_faces", 0),
        "last_recognition": status.get("last_recognition"),
        "system_health": "healthy" if status.get("active") else "inactive"
    }

@router.post("/start")
async def start_camera(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_camera_access)
):
    """Start camera processing"""
    try:
        camera_service = CameraService()
        result = await camera_service.start_processing()
        
        if result["success"]:
            return {"message": "Camera processing started successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to start camera")
            )
    except Exception as e:
        logger.error(f"Error starting camera: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start camera processing"
        )

@router.post("/stop")
async def stop_camera(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_camera_access)
):
    """Stop camera processing"""
    try:
        camera_service = CameraService()
        result = await camera_service.stop_processing()
        
        if result["success"]:
            return {"message": "Camera processing stopped successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to stop camera")
            )
    except Exception as e:
        logger.error(f"Error stopping camera: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop camera processing"
        )

@router.websocket("/feed")
async def camera_feed_websocket(websocket: WebSocket):
    """WebSocket endpoint for live camera feed"""
    await manager.connect(websocket)
    
    try:
        camera_service = CameraService()
        
        # Start camera if not already running
        await camera_service.start_processing()
        
        while True:
            # Get latest frame from camera service
            frame_data = await camera_service.get_latest_frame()
            
            if frame_data:
                # Send frame data to client
                await manager.send_personal_message(
                    json.dumps({
                        "type": "frame",
                        "data": frame_data["frame"],
                        "detections": frame_data.get("detections", []),
                        "timestamp": frame_data.get("timestamp")
                    }),
                    websocket
                )
            
            # Send at ~30 FPS
            await asyncio.sleep(1/30)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Camera feed WebSocket disconnected")
    except Exception as e:
        logger.error(f"Camera feed WebSocket error: {e}")
        manager.disconnect(websocket)

@router.websocket("/events")
async def camera_events_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time recognition events"""
    await manager.connect(websocket)
    
    try:
        camera_service = CameraService()
        
        while True:
            # Get latest recognition events
            events = await camera_service.get_latest_events()
            
            if events:
                for event in events:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "recognition_event",
                            "employee_id": event.get("employee_id"),
                            "employee_name": event.get("employee_name"),
                            "event_type": event.get("event_type"),
                            "confidence": event.get("confidence"),
                            "timestamp": event.get("timestamp"),
                            "camera_id": event.get("camera_id")
                        }),
                        websocket
                    )
            
            await asyncio.sleep(1)  # Check for events every second
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Camera events WebSocket disconnected")
    except Exception as e:
        logger.error(f"Camera events WebSocket error: {e}")
        manager.disconnect(websocket)

@router.get("/config")
async def get_camera_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_camera_access)
):
    """Get camera configuration"""
    camera_service = CameraService()
    config = await camera_service.get_config()
    
    return config

@router.put("/config")
async def update_camera_config(
    config_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_camera_access)
):
    """Update camera configuration"""
    try:
        camera_service = CameraService()
        result = await camera_service.update_config(config_data)
        
        if result["success"]:
            return {"message": "Camera configuration updated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to update configuration")
            )
    except Exception as e:
        logger.error(f"Error updating camera config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update camera configuration"
        )