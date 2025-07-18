from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    role_name: str

class UserResponse(BaseModel):
    id: int
    username: str
    status: str
    role_name: str
    last_login_time: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None