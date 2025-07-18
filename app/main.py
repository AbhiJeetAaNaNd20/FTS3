from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os

from app.core.config import settings
from app.core.database import create_tables
from app.api.routes import auth, employees, attendance, admin, camera
from app.services.face_recognition_service import FaceRecognitionService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Global face recognition service instance
face_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global face_service
    
    # Startup
    logger.info("Starting Facial Recognition System...")
    
    # Create database tables
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise
    
    # Initialize face recognition service
    try:
        face_service = FaceRecognitionService()
        await face_service.initialize()
        app.state.face_service = face_service
        logger.info("Face recognition service initialized")
    except Exception as e:
        logger.error(f"Error initializing face recognition service: {e}")
        raise
    
    # Create upload directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Facial Recognition System...")
    if face_service:
        await face_service.cleanup()

# Create FastAPI app
app = FastAPI(
    title="Facial Recognition System",
    description="Employee attendance and tracking system with facial recognition",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(employees.router, prefix="/api/employees", tags=["employees"])
app.include_router(attendance.router, prefix="/api/attendance", tags=["attendance"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(camera.router, prefix="/api/camera", tags=["camera"])

# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Facial Recognition System API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "facial-recognition-system"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )