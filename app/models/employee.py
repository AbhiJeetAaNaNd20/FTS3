from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

class Employee(Base):
    __tablename__ = 'employees'
    
    id = Column(String, primary_key=True, index=True)
    employee_name = Column(String, nullable=False)
    department = Column(String)
    designation = Column(String)
    email = Column(String)
    phone = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    embeddings = relationship("FaceEmbedding", back_populates="employee", cascade="all, delete-orphan")
    attendance_records = relationship("AttendanceRecord", back_populates="employee", cascade="all, delete-orphan")
    tracking_records = relationship("TrackingRecord", back_populates="employee", cascade="all, delete-orphan")