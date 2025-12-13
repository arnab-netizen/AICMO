"""Identity - DTOs."""
from pydantic import BaseModel
from typing import List, Optional
from aicmo.shared.ids import UserId

class UserDTO(BaseModel):
    user_id: UserId
    username: str
    email: str
    roles: List[str]

class AuthContextDTO(BaseModel):
    user: UserDTO
    token: str
    expires_at: Optional[str] = None

class PermissionDTO(BaseModel):
    resource: str
    actions: List[str]

__all__ = ["UserDTO", "AuthContextDTO", "PermissionDTO"]
