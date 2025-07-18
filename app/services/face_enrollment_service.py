import os
import cv2
import numpy as np
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from insightface.app import FaceAnalysis

from app.models.employee import Employee
from app.models.face_embedding import FaceEmbedding
from app.core.config import settings

logger = logging.getLogger(__name__)

class FaceEnrollmentService:
    """Service for face enrollment operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.face_app = None
        self._initialize_face_app()
    
    def _initialize_face_app(self):
        """Initialize InsightFace application"""
        try:
            self.face_app = FaceAnalysis(
                name='antelopev2',
                providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
            )
            self.face_app.prepare(ctx_id=0, det_size=(416, 416))
            logger.info("Face analysis app initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing face analysis app: {e}")
            raise
    
    async def enroll_from_images(self, employee_id: str, image_paths: List[str], 
                                update_existing: bool = False, min_faces: int = 1) -> Dict:
        """Enroll face embeddings from image files"""
        try:
            # Validate employee exists
            employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
            if not employee:
                return {"success": False, "error": "Employee not found"}
            
            if not image_paths:
                return {"success": False, "error": "No image paths provided"}
            
            processed_count = 0
            errors = []
            
            for img_path in image_paths:
                try:
                    if not os.path.exists(img_path):
                        errors.append(f"Image not found: {img_path}")
                        continue
                    
                    # Read and process image
                    img = cv2.imread(img_path)
                    if img is None:
                        errors.append(f"Could not read image: {img_path}")
                        continue
                    
                    # Detect faces
                    faces = self.face_app.get(img)
                    if len(faces) != 1:
                        errors.append(f"Expected 1 face, found {len(faces)} in {img_path}")
                        continue
                    
                    face = faces[0]
                    
                    # Validate embedding
                    if not self._validate_embedding(face.embedding):
                        errors.append(f"Invalid embedding from {img_path}")
                        continue
                    
                    # Store embedding in database
                    success = await self._store_embedding(
                        employee_id=employee_id,
                        embedding=face.embedding,
                        embedding_type='update' if update_existing else 'enroll',
                        quality_score=float(face.det_score),
                        source_image_path=img_path
                    )
                    
                    if success:
                        processed_count += 1
                        logger.info(f"Processed embedding from {img_path}")
                    else:
                        errors.append(f"Failed to store embedding from {img_path}")
                
                except Exception as e:
                    errors.append(f"Error processing {img_path}: {str(e)}")
                    logger.error(f"Error processing {img_path}: {e}")
            
            if processed_count >= min_faces:
                return {
                    "success": True,
                    "processed_count": processed_count,
                    "total_files": len(image_paths),
                    "errors": errors
                }
            else:
                return {
                    "success": False,
                    "error": f"Only {processed_count} valid faces found (minimum {min_faces} required)",
                    "processed_count": processed_count,
                    "errors": errors
                }
        
        except Exception as e:
            logger.error(f"Error in enroll_from_images: {e}")
            return {"success": False, "error": str(e)}
    
    async def _store_embedding(self, employee_id: str, embedding: np.ndarray,
                              embedding_type: str, quality_score: float,
                              source_image_path: str) -> bool:
        """Store face embedding in database"""
        try:
            import pickle
            
            embedding_data = pickle.dumps(embedding)
            
            face_embedding = FaceEmbedding(
                employee_id=employee_id,
                embedding_data=embedding_data,
                embedding_type=embedding_type,
                quality_score=quality_score,
                source_image_path=source_image_path
            )
            
            self.db.add(face_embedding)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error storing embedding: {e}")
            return False
    
    def _validate_embedding(self, embedding: np.ndarray) -> bool:
        """Validate embedding format"""
        return (
            isinstance(embedding, np.ndarray) and 
            embedding.dtype == np.float32 and 
            len(embedding.shape) == 1 and
            embedding.shape[0] > 0
        )
    
    async def delete_embedding(self, embedding_id: int) -> bool:
        """Delete (deactivate) a face embedding"""
        try:
            embedding = self.db.query(FaceEmbedding).filter(
                FaceEmbedding.id == embedding_id
            ).first()
            
            if not embedding:
                return False
            
            embedding.is_active = False
            self.db.commit()
            
            logger.info(f"Deactivated embedding {embedding_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting embedding {embedding_id}: {e}")
            return False
    
    async def get_employee_embeddings(self, employee_id: str) -> List[Dict]:
        """Get all embeddings for an employee"""
        try:
            embeddings = self.db.query(FaceEmbedding).filter(
                FaceEmbedding.employee_id == employee_id,
                FaceEmbedding.is_active == True
            ).order_by(FaceEmbedding.created_at.desc()).all()
            
            return [
                {
                    "id": emb.id,
                    "embedding_type": emb.embedding_type,
                    "quality_score": emb.quality_score,
                    "source_image_path": emb.source_image_path,
                    "created_at": emb.created_at,
                    "is_active": emb.is_active
                }
                for emb in embeddings
            ]
            
        except Exception as e:
            logger.error(f"Error getting embeddings for {employee_id}: {e}")
            return []
    
    async def cleanup_old_embeddings(self, employee_id: str, max_embeddings: int = 25) -> int:
        """Clean up old embeddings for an employee"""
        try:
            # Get update embeddings sorted by creation date
            update_embeddings = self.db.query(FaceEmbedding).filter(
                FaceEmbedding.employee_id == employee_id,
                FaceEmbedding.embedding_type == 'update',
                FaceEmbedding.is_active == True
            ).order_by(FaceEmbedding.created_at.desc()).all()
            
            if len(update_embeddings) <= max_embeddings:
                return 0
            
            # Deactivate old embeddings
            embeddings_to_deactivate = update_embeddings[max_embeddings:]
            deactivated_count = 0
            
            for embedding in embeddings_to_deactivate:
                embedding.is_active = False
                deactivated_count += 1
            
            self.db.commit()
            
            logger.info(f"Deactivated {deactivated_count} old embeddings for {employee_id}")
            return deactivated_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cleaning up embeddings for {employee_id}: {e}")
            return 0