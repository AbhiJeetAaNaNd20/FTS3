from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid

from app.core.database import get_db
from app.models.employee import Employee
from app.models.face_embedding import FaceEmbedding
from app.models.user import User
from app.schemas.employee import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse, 
    EmployeeListResponse, FaceEmbeddingResponse
)
from app.api.dependencies import get_current_active_user, require_enrollment
from app.services.face_enrollment_service import FaceEnrollmentService
from app.core.config import settings

router = APIRouter()

@router.get("/", response_model=EmployeeListResponse)
async def get_employees(
    page: int = 1,
    per_page: int = 50,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of employees"""
    query = db.query(Employee).filter(Employee.is_active == True)
    
    if search:
        query = query.filter(
            Employee.employee_name.ilike(f"%{search}%") |
            Employee.id.ilike(f"%{search}%")
        )
    
    total = query.count()
    employees = query.offset((page - 1) * per_page).limit(per_page).all()
    
    # Add embedding count for each employee
    employee_responses = []
    for emp in employees:
        embedding_count = db.query(FaceEmbedding).filter(
            FaceEmbedding.employee_id == emp.id,
            FaceEmbedding.is_active == True
        ).count()
        
        emp_response = EmployeeResponse(
            id=emp.id,
            employee_name=emp.employee_name,
            department=emp.department,
            designation=emp.designation,
            email=emp.email,
            phone=emp.phone,
            is_active=emp.is_active,
            created_at=emp.created_at,
            updated_at=emp.updated_at,
            embedding_count=embedding_count
        )
        employee_responses.append(emp_response)
    
    return EmployeeListResponse(
        employees=employee_responses,
        total=total,
        page=page,
        per_page=per_page
    )

@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get employee by ID"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    embedding_count = db.query(FaceEmbedding).filter(
        FaceEmbedding.employee_id == employee_id,
        FaceEmbedding.is_active == True
    ).count()
    
    return EmployeeResponse(
        id=employee.id,
        employee_name=employee.employee_name,
        department=employee.department,
        designation=employee.designation,
        email=employee.email,
        phone=employee.phone,
        is_active=employee.is_active,
        created_at=employee.created_at,
        updated_at=employee.updated_at,
        embedding_count=embedding_count
    )

@router.post("/", response_model=EmployeeResponse)
async def create_employee(
    employee_data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_enrollment)
):
    """Create a new employee"""
    # Check if employee ID already exists
    existing = db.query(Employee).filter(Employee.id == employee_data.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee ID already exists"
        )
    
    employee = Employee(**employee_data.dict())
    db.add(employee)
    db.commit()
    db.refresh(employee)
    
    return EmployeeResponse(
        id=employee.id,
        employee_name=employee.employee_name,
        department=employee.department,
        designation=employee.designation,
        email=employee.email,
        phone=employee.phone,
        is_active=employee.is_active,
        created_at=employee.created_at,
        updated_at=employee.updated_at,
        embedding_count=0
    )

@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: str,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_enrollment)
):
    """Update employee information"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Update only provided fields
    update_data = employee_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)
    
    db.commit()
    db.refresh(employee)
    
    embedding_count = db.query(FaceEmbedding).filter(
        FaceEmbedding.employee_id == employee_id,
        FaceEmbedding.is_active == True
    ).count()
    
    return EmployeeResponse(
        id=employee.id,
        employee_name=employee.employee_name,
        department=employee.department,
        designation=employee.designation,
        email=employee.email,
        phone=employee.phone,
        is_active=employee.is_active,
        created_at=employee.created_at,
        updated_at=employee.updated_at,
        embedding_count=embedding_count
    )

@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_enrollment)
):
    """Delete an employee and all related data"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Delete employee (cascade will handle related records)
    db.delete(employee)
    db.commit()
    
    return {"message": f"Employee {employee_id} deleted successfully"}

@router.post("/{employee_id}/enroll")
async def enroll_employee_faces(
    employee_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_enrollment)
):
    """Enroll face images for an employee"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )
    
    # Save uploaded files
    saved_files = []
    upload_dir = os.path.join(settings.UPLOAD_DIR, employee_id)
    os.makedirs(upload_dir, exist_ok=True)
    
    try:
        for file in files:
            if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file type: {file.content_type}"
                )
            
            # Generate unique filename
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                content = await file.read()
                if len(content) > settings.MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="File too large"
                    )
                buffer.write(content)
            
            saved_files.append(file_path)
        
        # Process faces using enrollment service
        enrollment_service = FaceEnrollmentService(db)
        result = await enrollment_service.enroll_from_images(
            employee_id, saved_files, update_existing=True
        )
        
        if result["success"]:
            return {
                "message": f"Successfully enrolled {result['processed_count']} faces for employee {employee_id}",
                "processed_count": result["processed_count"],
                "total_files": len(files)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
    
    except Exception as e:
        # Clean up saved files on error
        for file_path in saved_files:
            if os.path.exists(file_path):
                os.remove(file_path)
        raise

@router.get("/{employee_id}/embeddings", response_model=List[FaceEmbeddingResponse])
async def get_employee_embeddings(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_enrollment)
):
    """Get all embeddings for an employee"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    embeddings = db.query(FaceEmbedding).filter(
        FaceEmbedding.employee_id == employee_id,
        FaceEmbedding.is_active == True
    ).order_by(FaceEmbedding.created_at.desc()).all()
    
    return [
        FaceEmbeddingResponse(
            id=emb.id,
            employee_id=emb.employee_id,
            embedding_type=emb.embedding_type,
            quality_score=emb.quality_score,
            source_image_path=emb.source_image_path,
            created_at=emb.created_at,
            is_active=emb.is_active
        )
        for emb in embeddings
    ]

@router.delete("/{employee_id}/embeddings/{embedding_id}")
async def delete_embedding(
    employee_id: str,
    embedding_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_enrollment)
):
    """Delete a specific embedding"""
    embedding = db.query(FaceEmbedding).filter(
        FaceEmbedding.id == embedding_id,
        FaceEmbedding.employee_id == employee_id
    ).first()
    
    if not embedding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Embedding not found"
        )
    
    # Mark as inactive instead of deleting
    embedding.is_active = False
    db.commit()
    
    return {"message": "Embedding deleted successfully"}