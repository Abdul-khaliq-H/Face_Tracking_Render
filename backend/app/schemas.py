from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models import JobStatus


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: EmailStr


class JobResponse(BaseModel):
    id: int
    status: JobStatus
    progress: int
    error_message: str | None
    input_url: str
    output_url: str | None
    download_url: str | None
    created_at: datetime


class MessageResponse(BaseModel):
    message: str

