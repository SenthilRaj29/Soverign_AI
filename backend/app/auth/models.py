from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
import time

class UserRole(str, Enum):
    ENGINEER = "ENGINEER"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"

class User(BaseModel):
    id: str
    username: str
    role: UserRole
    is_active: bool = True
    created_at: float = Field(default_factory=time.time)

    model_config = ConfigDict(extra="forbid")

class UserInDB(User):
    password_hash: str

    model_config = ConfigDict(extra="forbid")

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User

    model_config = ConfigDict(extra="forbid")

class TokenData(BaseModel):
    sub: str
    username: str
    role: UserRole
    exp: Optional[int] = None

    model_config = ConfigDict(extra="forbid")

class LoginRequest(BaseModel):
    username: str
    password: str

    model_config = ConfigDict(extra="forbid")

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    model_config = ConfigDict(extra="forbid")
