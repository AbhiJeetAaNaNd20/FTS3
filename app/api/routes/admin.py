from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import List

from app.core.database import get_db
from app.models.employee import Employee
from app.models.attendance import AttendanceRecord, SystemLog
from app.models.face_embedding import FaceEmbedding
from app.models.user import User, Role
from app.schemas.auth import UserResponse, UserCreate
from app.api.dependencies import require_admin, require_super_admin
from app.core.security import get_password_hash

router = APIRouter()

@router.get("/dashboard")
async def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get admin dashboard statistics"""
    # Employee statistics
    total_employees = db.query(Employee).filter(Employee.is_active == True).count()
    total_embeddings = db.query(FaceEmbedding).filter(FaceEmbedding.is_active == True).count()
    
    # Today's attendance
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    today_checkins = db.query(AttendanceRecord).filter(
        AttendanceRecord.event_type == 'check_in',
        AttendanceRecord.timestamp >= today_start,
        AttendanceRecord.timestamp <= today_end,
        AttendanceRecord.is_valid == True
    ).count()
    
    today_checkouts = db.query(AttendanceRecord).filter(
        AttendanceRecord.event_type == 'check_out',
        AttendanceRecord.timestamp >= today_start,
        AttendanceRecord.timestamp <= today_end,
        AttendanceRecord.is_valid == True
    ).count()
    
    # Recent activity
    recent_attendance = db.query(AttendanceRecord, Employee).join(
        Employee, AttendanceRecord.employee_id == Employee.id
    ).filter(
        AttendanceRecord.is_valid == True
    ).order_by(desc(AttendanceRecord.timestamp)).limit(10).all()
    
    recent_activity = []
    for record, employee in recent_attendance:
        recent_activity.append({
            "employee_id": record.employee_id,
            "employee_name": employee.employee_name,
            "event_type": record.event_type,
            "timestamp": record.timestamp,
            "confidence_score": record.confidence_score
        })
    
    # System health
    system_logs_count = db.query(SystemLog).filter(
        SystemLog.timestamp >= datetime.now() - timedelta(hours=24)
    ).count()
    
    error_logs_count = db.query(SystemLog).filter(
        SystemLog.log_level == 'ERROR',
        SystemLog.timestamp >= datetime.now() - timedelta(hours=24)
    ).count()
    
    return {
        "statistics": {
            "total_employees": total_employees,
            "total_embeddings": total_embeddings,
            "today_checkins": today_checkins,
            "today_checkouts": today_checkouts
        },
        "recent_activity": recent_activity,
        "system_health": {
            "total_logs_24h": system_logs_count,
            "error_logs_24h": error_logs_count,
            "system_status": "healthy" if error_logs_count < 10 else "warning"
        }
    }

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Get all users (Super Admin only)"""
    users = db.query(User).join(Role).all()
    
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            status=user.status,
            role_name=user.role.role_name,
            last_login_time=user.last_login_time,
            created_at=user.created_at
        )
        for user in users
    ]

@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Update user status (Super Admin only)"""
    if status not in ['active', 'inactive', 'suspended']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Must be 'active', 'inactive', or 'suspended'"
        )
    
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own status"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.status = status
    db.commit()
    
    return {"message": f"User status updated to {status}"}

@router.get("/system-logs")
async def get_system_logs(
    page: int = 1,
    per_page: int = 50,
    log_level: str = None,
    component: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get system logs"""
    query = db.query(SystemLog)
    
    if log_level:
        query = query.filter(SystemLog.log_level == log_level.upper())
    
    if component:
        query = query.filter(SystemLog.component == component)
    
    query = query.order_by(desc(SystemLog.timestamp))
    
    total = query.count()
    logs = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "log_level": log.log_level,
                "message": log.message,
                "component": log.component,
                "employee_id": log.employee_id,
                "camera_id": log.camera_id,
                "timestamp": log.timestamp,
                "additional_data": log.additional_data
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "per_page": per_page
    }

@router.get("/roles")
async def get_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Get all roles (Super Admin only)"""
    roles = db.query(Role).all()
    
    return [
        {
            "id": role.id,
            "role_name": role.role_name,
            "permissions": role.permissions,
            "user_count": len(role.users),
            "created_at": role.created_at
        }
        for role in roles
    ]

@router.delete("/system-logs/cleanup")
async def cleanup_old_logs(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Clean up old system logs (Super Admin only)"""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    deleted_count = db.query(SystemLog).filter(
        SystemLog.timestamp < cutoff_date
    ).delete()
    
    db.commit()
    
    return {
        "message": f"Cleaned up {deleted_count} log entries older than {days} days",
        "deleted_count": deleted_count
    }