import base64
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
import logging

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from pydantic import ValidationError
from sqlalchemy.orm import Session

from . import models, schemas
from .database import get_db
from .config import JWT_SECRET, JWT_ISSUER, JWT_AUDIENCE, JWT_EXPIRE_MINUTES

# Configure logging
logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    scopes={
        "admin": "Full access to all operations",
        "manager": "Manage inventory and warehouse operations",
        "user": "Basic access to view and perform basic operations",
    }
)

# Role-based access control configuration
ROLE_PERMISSIONS = {
    "admin": ["read", "write", "update", "delete", "admin"],
    "manager": ["read", "write", "update"],
    "user": ["read"],
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    return pwd_context.hash(password)

def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None,
    scopes: Optional[List[str]] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: The data to include in the token
        expires_delta: Optional expiration time delta
        scopes: List of scopes to include in the token
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=JWT_EXPIRE_MINUTES)
    
    # Standard claims
    to_encode.update({
        "exp": expire,
        "iat": now,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "scopes": scopes or ["user"],
    })
    
    return jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")

def create_refresh_token(
    user_id: int,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a refresh token for a user."""
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=30)  # 30 days for refresh tokens
    
    to_encode = {
        "sub": f"refresh:{user_id}",
        "exp": expire,
        "iat": now,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "type": "refresh",
    }
    
    return jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")

async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Dependency to get the current authenticated user.
    
    Validates the JWT token and checks if the user has the required scopes.
    """
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    
    try:
        # Decode and validate the JWT token
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )
        
        # Extract user identity from token
        user_id: int = int(payload.get("sub", "").split(":")[-1])
        if not user_id:
            raise credentials_exception
            
        # Check token type (access or refresh)
        token_type = payload.get("type", "access")
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token type",
                headers={"WWW-Authenticate": authenticate_value},
            )
        
        # Get user from database
        user = db.query(models.User).filter(
            models.User.id == user_id,
            models.User.is_active == True,
            models.User.is_deleted == False
        ).first()
        
        if not user:
            raise credentials_exception
            
        # Check if the user has the required scopes
        token_scopes = payload.get("scopes", [])
        if security_scopes.scopes:
            for scope in security_scopes.scopes:
                if scope not in token_scopes:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not enough permissions",
                        headers={"WWW-Authenticate": authenticate_value},
                    )
        
        return user
        
    except (JWTError, ValidationError) as e:
        logger.error(f"Token validation error: {str(e)}")
        raise credentials_exception

def get_current_active_user(
    current_user: models.User = Security(get_current_user, scopes=["user"])
) -> models.User:
    """Dependency to get the current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

def has_permission(user: models.User, required_permission: str) -> bool:
    """Check if a user has a specific permission."""
    if not user or not user.user_role:
        return False
    user_permissions = ROLE_PERMISSIONS.get(user.user_role.lower(), [])
    return required_permission in user_permissions

def require_permission(permission: str):
    """Dependency to check if user has a specific permission."""
    def dependency(
        current_user: models.User = Depends(get_current_active_user)
    ) -> models.User:
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return dependency

# Common permission dependencies
require_admin = require_permission("admin")
require_manager = require_permission("write")
require_read = require_permission("read")
