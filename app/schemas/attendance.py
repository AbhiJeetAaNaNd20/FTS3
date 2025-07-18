from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AttendanceRecordResponse(BaseModel):
    id: int
    employee_id: str
    employee_name: str
    camera_id: int
    event_type: str
    timestamp: datetime
    confidence_score: Optional[float]
    work_status: str
    is_valid: bool
    notes: Optional[str]

    class Config:
        from_attributes = True

class AttendanceListResponse(BaseModel):
    records: List[AttendanceRecordResponse]
    total: int
    page: int
    per_page: int

class EmployeeStatusResponse(BaseModel):
    employee_id: str
    employee_name: str
    is_present: bool
    last_event: Optional[str]
    last_timestamp: Optional[datetime]

class PresentEmployeesResponse(BaseModel):
    present_employees: List[EmployeeStatusResponse]
    total_present: int
    last_updated: datetime