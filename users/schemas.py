from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional

class RegisterSchema(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "student"


class LoginSchema(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: str
    role: str
    bio: Optional[str] = None

class ProfileUpdateSchema(BaseModel):
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
