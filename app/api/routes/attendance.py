from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, date, timedelta
from typing import Optional, List

from app.core.database import get_db
from app.models.employee import Employee
from app.models.attendance import AttendanceRecord
from app.models.user import User
from app.schemas.attendance import (
    AttendanceRecordResponse, AttendanceListResponse,
    EmployeeStatusResponse, PresentEmployeesResponse
)
from app.api.dependencies import get_current_active_user, require_admin

router = APIRouter()

@router.get("/", response_model=AttendanceListResponse)
async def get_attendance_records(
    page: int = 1,
    per_page: int = 50,
    employee_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get attendance records"""
    # Regular employees can only view their own records
    if current_user.role.role_name == "employee":
        if employee_id and employee_id != current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only view your own attendance records"
            )
        employee_id = current_user.username
    
    query = db.query(AttendanceRecord, Employee).join(
        Employee, AttendanceRecord.employee_id == Employee.id
    ).filter(AttendanceRecord.is_valid == True)
    
    if employee_id:
        query = query.filter(AttendanceRecord.employee_id == employee_id)
    
    if start_date:
        query = query.filter(AttendanceRecord.timestamp >= start_date)
    
    if end_date:
        # Include the entire end date
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(AttendanceRecord.timestamp <= end_datetime)
    
    if event_type:
        query = query.filter(AttendanceRecord.event_type == event_type)
    
    query = query.order_by(desc(AttendanceRecord.timestamp))
    
    total = query.count()
    results = query.offset((page - 1) * per_page).limit(per_page).all()
    
    records = []
    for attendance, employee in results:
        records.append(AttendanceRecordResponse(
            id=attendance.id,
            employee_id=attendance.employee_id,
            employee_name=employee.employee_name,
            camera_id=attendance.camera_id,
            event_type=attendance.event_type,
            timestamp=attendance.timestamp,
            confidence_score=attendance.confidence_score,
            work_status=attendance.work_status,
            is_valid=attendance.is_valid,
            notes=attendance.notes
        ))
    
    return AttendanceListResponse(
        records=records,
        total=total,
        page=page,
        per_page=per_page
    )

@router.get("/present", response_model=PresentEmployeesResponse)
async def get_present_employees(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of currently present employees"""
    # Get latest attendance record for each employee
    subquery = db.query(
        AttendanceRecord.employee_id,
        AttendanceRecord.event_type,
        AttendanceRecord.timestamp,
        desc(AttendanceRecord.timestamp).label('latest_timestamp')
    ).filter(
        AttendanceRecord.is_valid == True,
        AttendanceRecord.timestamp >= datetime.now() - timedelta(hours=24)
    ).group_by(AttendanceRecord.employee_id).subquery()
    
    # Get employees with their latest attendance status
    query = db.query(Employee, subquery.c.event_type, subquery.c.timestamp).join(
        subquery, Employee.id == subquery.c.employee_id, isouter=True
    ).filter(Employee.is_active == True)
    
    results = query.all()
    present_employees = []
    
    for employee, last_event, last_timestamp in results:
        is_present = last_event == 'check_in' if last_event else False
        
        present_employees.append(EmployeeStatusResponse(
            employee_id=employee.id,
            employee_name=employee.employee_name,
            is_present=is_present,
            last_event=last_event,
            last_timestamp=last_timestamp
        ))
    
    # Filter only present employees for the count
    total_present = sum(1 for emp in present_employees if emp.is_present)
    
    return PresentEmployeesResponse(
        present_employees=present_employees,
        total_present=total_present,
        last_updated=datetime.now()
    )

@router.get("/employee/{employee_id}", response_model=AttendanceListResponse)
async def get_employee_attendance(
    employee_id: str,
    page: int = 1,
    per_page: int = 50,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get attendance records for a specific employee"""
    # Regular employees can only view their own records
    if current_user.role.role_name == "employee" and employee_id != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own attendance records"
        )
    
    # Check if employee exists
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    query = db.query(AttendanceRecord).filter(
        AttendanceRecord.employee_id == employee_id,
        AttendanceRecord.is_valid == True
    )
    
    if start_date:
        query = query.filter(AttendanceRecord.timestamp >= start_date)
    
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(AttendanceRecord.timestamp <= end_datetime)
    
    query = query.order_by(desc(AttendanceRecord.timestamp))
    
    total = query.count()
    records = query.offset((page - 1) * per_page).limit(per_page).all()
    
    attendance_records = []
    for record in records:
        attendance_records.append(AttendanceRecordResponse(
            id=record.id,
            employee_id=record.employee_id,
            employee_name=employee.employee_name,
            camera_id=record.camera_id,
            event_type=record.event_type,
            timestamp=record.timestamp,
            confidence_score=record.confidence_score,
            work_status=record.work_status,
            is_valid=record.is_valid,
            notes=record.notes
        ))
    
    return AttendanceListResponse(
        records=attendance_records,
        total=total,
        page=page,
        per_page=per_page
    )

@router.get("/summary/{employee_id}")
async def get_attendance_summary(
    employee_id: str,
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get attendance summary for an employee"""
    # Regular employees can only view their own summary
    if current_user.role.role_name == "employee" and employee_id != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own attendance summary"
        )
    
    # Default to current month if no dates provided
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        end_date = date.today()
    
    # Check if employee exists
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Get attendance records for the period
    records = db.query(AttendanceRecord).filter(
        AttendanceRecord.employee_id == employee_id,
        AttendanceRecord.is_valid == True,
        AttendanceRecord.timestamp >= start_date,
        AttendanceRecord.timestamp <= datetime.combine(end_date, datetime.max.time())
    ).order_by(AttendanceRecord.timestamp).all()
    
    # Calculate summary statistics
    total_days = (end_date - start_date).days + 1
    check_ins = len([r for r in records if r.event_type == 'check_in'])
    check_outs = len([r for r in records if r.event_type == 'check_out'])
    
    # Calculate working days (assuming 5-day work week)
    working_days = 0
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Monday = 0, Friday = 4
            working_days += 1
        current_date += timedelta(days=1)
    
    return {
        "employee_id": employee_id,
        "employee_name": employee.employee_name,
        "period": {
            "start_date": start_date,
            "end_date": end_date,
            "total_days": total_days,
            "working_days": working_days
        },
        "summary": {
            "total_check_ins": check_ins,
            "total_check_outs": check_outs,
            "attendance_rate": round((check_ins / working_days * 100), 2) if working_days > 0 else 0
        },
        "records_count": len(records)
    }