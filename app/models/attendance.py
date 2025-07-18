from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

class AttendanceRecord(Base):
    __tablename__ = 'attendance_records'
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, ForeignKey('employees.id'), nullable=False)
    camera_id = Column(Integer, nullable=False)
    event_type = Column(String, nullable=False)  # check_in, check_out
    timestamp = Column(DateTime, default=func.now())
    confidence_score = Column(Float)
    work_status = Column(String, default='working')
    is_valid = Column(Boolean, default=True)
    notes = Column(Text)
    
    # Relationships
    employee = relationship("Employee", back_populates="attendance_records")

class TrackingRecord(Base):
    __tablename__ = 'tracking_records'
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, ForeignKey('employees.id'), nullable=False)
    camera_id = Column(Integer, nullable=False)
    position_x = Column(Float)
    position_y = Column(Float)
    confidence_score = Column(Float)
    quality_metrics = Column(JSON)
    timestamp = Column(DateTime, default=func.now())
    tracking_state = Column(String, default='active')
    
    # Relationships
    employee = relationship("Employee", back_populates="tracking_records")

class SystemLog(Base):
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    log_level = Column(String, default='INFO')
    message = Column(Text, nullable=False)
    component = Column(String)
    employee_id = Column(String)
    camera_id = Column(Integer)
    timestamp = Column(DateTime, default=func.now())
    additional_data = Column(JSON)