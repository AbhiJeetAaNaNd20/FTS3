from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import verify_token, check_permissions
from app.models.user import User
from app.schemas.auth import TokenData

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    token_data = verify_token(token)
    
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if user.status != 'active':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    return current_user

def require_permissions(permissions: list):
    """Decorator to require specific permissions"""
    def permission_checker(current_user: User = Depends(get_current_active_user)):
        if not check_permissions(current_user.role.role_name, permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return permission_checker

# Common permission dependencies
require_admin = require_permissions(["view_all_attendance"])
require_super_admin = require_permissions(["manage_users"])
require_enrollment = require_permissions(["enroll_employees"])
require_camera_access = require_permissions(["view_camera_feed"])