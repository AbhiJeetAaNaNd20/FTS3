from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

class FaceEmbedding(Base):
    __tablename__ = 'face_embeddings'
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, ForeignKey('employees.id'), nullable=False)
    embedding_data = Column(LargeBinary, nullable=False)
    embedding_type = Column(String, default='enroll')  # enroll, update
    quality_score = Column(Float)
    source_image_path = Column(String)
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    employee = relationship("Employee", back_populates="embeddings")