"""Authentication middleware for API endpoints."""
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from typing import Optional
from jose import JWTError, jwt
from datetime import datetime, timedelta
import secrets

from ...utils.config import settings
from ...utils.logger import api_logger

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


class AuthenticationError(HTTPException):
    """Custom authentication error."""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=401, detail=detail)


async def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)) -> dict:
    """
    Verify JWT token from Authorization header.
    
    Args:
        credentials: HTTPBearer credentials from Authorization header
        
    Returns:
        Decoded token payload
        
    Raises:
        AuthenticationError: If token is invalid or missing
    """
    if not credentials:
        raise AuthenticationError("Missing authentication token")
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=["HS256"]
        )
        
        # Check token expiration
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.now():
            raise AuthenticationError("Token has expired")
        
        return payload
        
    except JWTError as e:
        api_logger.warning(f"JWT verification failed: {str(e)}")
        raise AuthenticationError("Invalid authentication token")


async def verify_api_key(api_key: Optional[str] = Security(api_key_scheme)) -> str:
    """
    Verify API key from X-API-Key header.
    
    Args:
        api_key: API key from X-API-Key header
        
    Returns:
        API key if valid
        
    Raises:
        AuthenticationError: If API key is invalid or missing
    """
    if not api_key:
        raise AuthenticationError("Missing API key")
    
    # In production, validate against database or environment
    # For now, check against a configured API key
    valid_api_keys = [
        settings.secret_key,  # Using secret_key as a valid API key for now
        # Add more valid keys from environment or database
    ]
    
    if api_key not in valid_api_keys:
        api_logger.warning(f"Invalid API key attempted: {api_key[:10]}...")
        raise AuthenticationError("Invalid API key")
    
    return api_key


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in token
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(hours=24)
    
    to_encode.update({"exp": expire, "iat": datetime.now()})
    
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")
    return encoded_jwt


def get_current_user(token_data: dict = Depends(verify_token)) -> dict:
    """
    Get current authenticated user from token.
    
    Args:
        token_data: Decoded token payload
        
    Returns:
        User information from token
    """
    return {
        "user_id": token_data.get("sub"),
        "username": token_data.get("username"),
        "roles": token_data.get("roles", [])
    }


# Optional authentication (doesn't fail if missing)
async def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    api_key: Optional[str] = Security(api_key_scheme)
) -> Optional[dict]:
    """
    Optional authentication - returns user if authenticated, None otherwise.
    Useful for endpoints that have different behavior for authenticated vs anonymous users.
    """
    try:
        if credentials:
            return await verify_token(credentials)
        elif api_key:
            await verify_api_key(api_key)
            return {"auth_type": "api_key"}
    except AuthenticationError:
        pass
    
    return None


# Role-based access control
def require_role(required_role: str):
    """
    Dependency factory for role-based access control.
    
    Usage:
        @router.get("/admin")
        async def admin_endpoint(user: dict = Depends(require_role("admin"))):
            ...
    """
    def role_checker(user: dict = Depends(get_current_user)) -> dict:
        user_roles = user.get("roles", [])
        if required_role not in user_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Required role: {required_role}"
            )
        return user
    
    return role_checker
