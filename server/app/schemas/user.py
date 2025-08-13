from pydantic import BaseModel, EmailStr
from app.models.user import UserTier
from .workspace import Workspace

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    tier: UserTier
    selected_model: str | None = None
    
    workspaces: list[Workspace] = [] 
    
    class ConfigDict:
        from_attributes = True

class UserUsage(BaseModel):
    limit: int | str
    used: int
    remaining: int | str