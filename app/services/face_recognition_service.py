import asyncio
import logging
import numpy as np
import pickle
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
import threading
import time

from app.core.database import SessionLocal
from app.models.employee import Employee
from app.models.face_embedding import FaceEmbedding
from app.models.attendance import AttendanceRecord
from app.core.config import settings

logger = logging.getLogger(__name__)

class FaceRecognitionService:
    """Service for face recognition operations"""
    
    def __init__(self):
        self.embeddings: List[np.ndarray] = []
        self.labels: List[str] = []
        self.last_reload_time = 0
        self.reload_lock = threading.RLock()
        self.recognition_threshold = settings.FACE_RECOGNITION_THRESHOLD
        
    async def initialize(self):
        """Initialize the face recognition service"""
        try:
            await self.reload_embeddings()
            logger.info("Face recognition service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing face recognition service: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Face recognition service cleanup completed")
    
    def get_db_session(self) -> Session:
        """Get database session"""
        return SessionLocal()
    
    def close_db_session(self, session: Session):
        """Close database session"""
        try:
            session.close()
        except Exception as e:
            logger.error(f"Error closing database session: {e}")
    
    async def reload_embeddings(self):
        """Reload embeddings from database"""
        with self.reload_lock:
            session = self.get_db_session()
            try:
                logger.info("Reloading face embeddings from database...")
                
                # Get all active embeddings
                embeddings_query = session.query(FaceEmbedding).filter(
                    FaceEmbedding.is_active == True
                ).all()
                
                new_embeddings = []
                new_labels = []
                
                # Process enrollment embeddings first
                enroll_embeddings = [e for e in embeddings_query if e.embedding_type == 'enroll']
                for emb_record in enroll_embeddings:
                    try:
                        embedding_data = pickle.loads(emb_record.embedding_data)
                        if self._validate_embedding(embedding_data):
                            new_embeddings.append(embedding_data)
                            new_labels.append(emb_record.employee_id)
                    except Exception as e:
                        logger.error(f"Error loading embedding {emb_record.id}: {e}")
                
                # Process update embeddings (limit per employee)
                update_embeddings = [e for e in embeddings_query if e.embedding_type == 'update']
                update_embeddings.sort(key=lambda x: x.created_at, reverse=True)
                
                employee_update_count = {}
                for emb_record in update_embeddings:
                    emp_id = emb_record.employee_id
                    if emp_id not in employee_update_count:
                        employee_update_count[emp_id] = 0
                    
                    if employee_update_count[emp_id] < 3:  # Limit to 3 update embeddings per employee
                        try:
                            embedding_data = pickle.loads(emb_record.embedding_data)
                            if self._validate_embedding(embedding_data):
                                new_embeddings.append(embedding_data)
                                new_labels.append(emb_record.employee_id)
                                employee_update_count[emp_id] += 1
                        except Exception as e:
                            logger.error(f"Error loading update embedding {emb_record.id}: {e}")
                
                # Update instance variables
                self.embeddings = new_embeddings
                self.labels = new_labels
                self.last_reload_time = time.time()
                
                logger.info(f"Loaded {len(self.embeddings)} embeddings for {len(set(self.labels))} employees")
                
            except Exception as e:
                logger.error(f"Error reloading embeddings: {e}")
                raise
            finally:
                self.close_db_session(session)
    
    def _validate_embedding(self, embedding: np.ndarray) -> bool:
        """Validate embedding format"""
        return (
            isinstance(embedding, np.ndarray) and 
            embedding.dtype == np.float32 and 
            len(embedding.shape) == 1 and
            embedding.shape[0] > 0
        )
    
    async def recognize_face(self, face_embedding: np.ndarray) -> Optional[Dict]:
        """Recognize a face from its embedding"""
        if not self._validate_embedding(face_embedding):
            logger.error("Invalid face embedding format")
            return None
        
        if not self.embeddings:
            logger.warning("No embeddings loaded for recognition")
            return None
        
        try:
            # Calculate similarities with all known embeddings
            similarities = []
            for known_embedding in self.embeddings:
                similarity = self._calculate_similarity(face_embedding, known_embedding)
                similarities.append(similarity)
            
            # Find best match
            max_similarity = max(similarities)
            best_match_idx = similarities.index(max_similarity)
            
            if max_similarity >= self.recognition_threshold:
                employee_id = self.labels[best_match_idx]
                
                # Get employee details
                session = self.get_db_session()
                try:
                    employee = session.query(Employee).filter(
                        Employee.id == employee_id,
                        Employee.is_active == True
                    ).first()
                    
                    if employee:
                        return {
                            "employee_id": employee_id,
                            "employee_name": employee.employee_name,
                            "confidence": float(max_similarity),
                            "department": employee.department,
                            "designation": employee.designation
                        }
                finally:
                    self.close_db_session(session)
            
            return None
            
        except Exception as e:
            logger.error(f"Error during face recognition: {e}")
            return None
    
    def _calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            # Normalize embeddings
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    async def log_attendance(self, employee_id: str, event_type: str, 
                           confidence: float, camera_id: int = 1) -> bool:
        """Log attendance record"""
        session = self.get_db_session()
        try:
            # Check for duplicate recent entries (within 5 minutes)
            recent_threshold = time.time() - 300  # 5 minutes
            recent_record = session.query(AttendanceRecord).filter(
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.event_type == event_type,
                AttendanceRecord.timestamp >= recent_threshold
            ).first()
            
            if recent_record:
                logger.info(f"Skipping duplicate attendance record for {employee_id}")
                return False
            
            # Create new attendance record
            attendance_record = AttendanceRecord(
                employee_id=employee_id,
                camera_id=camera_id,
                event_type=event_type,
                confidence_score=confidence,
                work_status='working'
            )
            
            session.add(attendance_record)
            session.commit()
            
            logger.info(f"Logged {event_type} for employee {employee_id} with confidence {confidence}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error logging attendance: {e}")
            return False
        finally:
            self.close_db_session(session)
    
    async def get_employee_status(self, employee_id: str) -> Dict:
        """Get current status of an employee"""
        session = self.get_db_session()
        try:
            # Get employee details
            employee = session.query(Employee).filter(Employee.id == employee_id).first()
            if not employee:
                return {"error": "Employee not found"}
            
            # Get latest attendance record
            latest_record = session.query(AttendanceRecord).filter(
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.is_valid == True
            ).order_by(AttendanceRecord.timestamp.desc()).first()
            
            is_present = False
            last_event = None
            last_timestamp = None
            
            if latest_record:
                is_present = latest_record.event_type == 'check_in'
                last_event = latest_record.event_type
                last_timestamp = latest_record.timestamp
            
            return {
                "employee_id": employee_id,
                "employee_name": employee.employee_name,
                "is_present": is_present,
                "last_event": last_event,
                "last_timestamp": last_timestamp,
                "department": employee.department,
                "designation": employee.designation
            }
            
        except Exception as e:
            logger.error(f"Error getting employee status: {e}")
            return {"error": str(e)}
        finally:
            self.close_db_session(session)
    
    async def get_statistics(self) -> Dict:
        """Get recognition system statistics"""
        return {
            "total_embeddings": len(self.embeddings),
            "unique_employees": len(set(self.labels)),
            "last_reload_time": self.last_reload_time,
            "recognition_threshold": self.recognition_threshold
        }
    
    def should_reload_embeddings(self, force: bool = False) -> bool:
        """Check if embeddings should be reloaded"""
        if force:
            return True
        
        # Reload every 5 minutes or if no embeddings loaded
        return (time.time() - self.last_reload_time > 300) or not self.embeddings