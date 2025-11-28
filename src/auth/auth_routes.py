from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
import re

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    phone: str
    full_name: str
    date_of_birth: str
    gender: str
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain number')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if not re.match(r'^\+?[1-9]\d{9,14}$', v):
            raise ValueError('Invalid phone number format')
        return v

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict

@router.post("/register", response_model=LoginResponse)
async def register(data: RegisterRequest):
    from .auth_service import AuthService
    
    auth_service = AuthService()
    
    # Check if email already exists
    existing_user = await auth_service.get_user_by_email(data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = auth_service.hash_password(data.password)
    
    # Create user
    user = await auth_service.create_patient({
        "email": data.email,
        "password_hash": hashed_password,
        "phone": data.phone,
        "full_name": data.full_name,
        "date_of_birth": data.date_of_birth,
        "gender": data.gender,
        "emergency_contact": {
            "name": data.emergency_contact_name,
            "phone": data.emergency_contact_phone
        },
        "created_at": "NOW()",
        "email_verified": False
    })
    
    # Generate tokens
    access_token = auth_service.create_access_token(user["id"])
    refresh_token = auth_service.create_refresh_token(user["id"])
    
    # Send verification email (async)
    await auth_service.send_verification_email(user["email"], user["id"])
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "phone": user["phone"]
        }
    )

@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest):
    from .auth_service import AuthService
    
    auth_service = AuthService()
    
    # Get user by email
    user = await auth_service.get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not auth_service.verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check account status
    if user.get("status") == "suspended":
        raise HTTPException(status_code=403, detail="Account suspended")
    
    # Generate tokens
    access_token = auth_service.create_access_token(user["id"])
    refresh_token = auth_service.create_refresh_token(user["id"])
    
    # Log login
    await auth_service.log_login_event(user["id"])
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "phone": user["phone"],
            "email_verified": user["email_verified"]
        }
    )

@router.get("/me")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    from .jwt_handler import decode_token
    from .auth_service import AuthService
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    auth_service = AuthService()
    user = await auth_service.get_user_by_id(payload["user_id"])
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "phone": user["phone"],
        "date_of_birth": user["date_of_birth"],
        "gender": user["gender"],
        "emergency_contact": user.get("emergency_contact"),
        "email_verified": user["email_verified"],
        "created_at": user["created_at"]
    }

@router.post("/refresh")
async def refresh_token(refresh_token: str):
    from .jwt_handler import decode_token
    from .auth_service import AuthService
    
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    auth_service = AuthService()
    
    # Check if blacklisted
    if await auth_service.is_token_blacklisted(refresh_token):
        raise HTTPException(status_code=401, detail="Token revoked")
    
    # Generate new access token
    new_access_token = auth_service.create_access_token(payload["user_id"])
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    from .auth_service import AuthService
    
    token = credentials.credentials
    auth_service = AuthService()
    
    await auth_service.blacklist_token(token)
    
    return {"message": "Logged out successfully"}
