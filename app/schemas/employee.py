from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class EmployeeBase(BaseModel):
    employee_name: str
    department: Optional[str] = None
    designation: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class EmployeeCreate(EmployeeBase):
    id: str

class EmployeeUpdate(EmployeeBase):
    employee_name: Optional[str] = None

class EmployeeResponse(EmployeeBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    embedding_count: Optional[int] = 0

    class Config:
        from_attributes = True

class EmployeeListResponse(BaseModel):
    employees: List[EmployeeResponse]
    total: int
    page: int
    per_page: int

class FaceEmbeddingResponse(BaseModel):
    id: int
    employee_id: str
    embedding_type: str
    quality_score: Optional[float]
    source_image_path: Optional[str]
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True