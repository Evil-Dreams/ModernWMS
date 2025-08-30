from datetime import timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from .. import models, schemas
from ..database import get_db
from ..security import (
    verify_password, create_access_token, create_refresh_token,
    get_current_user, require_admin, require_manager, require_read,
    get_password_hash
)
from ..utils.hash import md5_hex
from ..cache import cache

router = APIRouter(tags=["Authentication"])

@router.post(
    "/login",
    response_model=schemas.ResultModel,
    summary="User login",
    description="Authenticate a user and return access and refresh tokens"
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    # Find user by username or user number
    user = db.execute(
        select(models.User).where(
            or_(
                models.User.user_name == form_data.username,
                models.User.user_num == form_data.username
            ),
            models.User.is_active == True,
            models.User.is_deleted == False
        )
    ).scalar_one_or_none()
    
    if not user:
        return schemas.result_error("Incorrect username or password", status.HTTP_400_BAD_REQUEST)
    
    # Verify password
    # Check if password is already hashed with MD5 (from frontend)
    incoming_pwd = form_data.password
    if len(incoming_pwd) != 32:  # Not an MD5 hash
        incoming_pwd = md5_hex(incoming_pwd)
    
    if not verify_password(incoming_pwd, user.password):
        return schemas.result_error("Incorrect username or password", status.HTTP_400_BAD_REQUEST)
    
    # Determine user scopes based on role
    scopes = ["user"]  # Default scope
    if user.user_role == "admin":
        scopes.extend(["admin", "manager"])
    elif user.user_role == "manager":
        scopes.append("manager")
    
    # Create tokens
    access_token_expires = timedelta(minutes=30)  # Short-lived access token
    access_token = create_access_token(
        data={"sub": f"user:{user.user_id}"},
        expires_delta=access_token_expires,
        scopes=scopes
    )
    
    refresh_token = create_refresh_token(user.user_id)
    
    # Store refresh token in cache
    cache.set_token(user.user_id, refresh_token, timedelta(days=30))
    
    # Prepare user data for response
    user_data = {
        "user_id": user.user_id,
        "user_name": user.user_name,
        "user_num": user.user_num,
        "user_role": user.user_role,
        "userrole_id": user.userrole_id,
        "tenant_id": int(user.tenant_id),
        "email": user.email,
        "phone": user.phone,
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": int(access_token_expires.total_seconds()),
        "refresh_token": refresh_token,
        "scopes": scopes
    }
    
    return schemas.result_success(user_data)

@router.post(
    "/refresh-token",
    response_model=schemas.ResultModel,
    summary="Refresh access token",
    description="Get a new access token using a refresh token"
)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Refresh an access token using a valid refresh token.
    """
    try:
        # Decode the refresh token
        payload = cache.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return schemas.result_error("Invalid refresh token", status.HTTP_400_BAD_REQUEST)
        
        # Extract user ID from subject (format: "refresh:user_id")
        user_id = int(payload.get("sub", ":").split(":")[-1])
        if not user_id:
            return schemas.result_error("Invalid token format", status.HTTP_400_BAD_REQUEST)
        
        # Get user from database
        user = db.execute(
            select(models.User).where(
                models.User.id == user_id,
                models.User.is_active == True,
                models.User.is_deleted == False
            )
        ).scalar_one_or_none()
        
        if not user:
            return schemas.result_error("User not found", status.HTTP_404_NOT_FOUND)
        
        # Create new access token
        scopes = ["user"]
        if user.user_role == "admin":
            scopes.extend(["admin", "manager"])
        elif user.user_role == "manager":
            scopes.append("manager")
        
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": f"user:{user.user_id}"},
            expires_delta=access_token_expires,
            scopes=scopes
        )
        
        # Optionally rotate refresh token (uncomment if needed)
        # new_refresh_token = create_refresh_token(user.user_id)
        # cache.set_token(user.user_id, new_refresh_token, timedelta(days=30))
        
        return schemas.result_success({
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds()),
            "refresh_token": refresh_token,  # or new_refresh_token if rotating
            "user_id": user.user_id,
            "scopes": scopes
        })
        
    except Exception as e:
        return schemas.result_error("Invalid refresh token", status.HTTP_400_BAD_REQUEST)

@router.post(
    "/logout",
    response_model=schemas.ResultModel,
    summary="Logout user",
    description="Invalidate the current user's refresh token"
)
async def logout(
    current_user: models.User = Security(get_current_user, scopes=["user"]),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Log out the current user by invalidating their refresh token.
    """
    cache.delete_token(current_user.user_id)
    return schemas.result_success("Successfully logged out")

@router.get(
    "/me",
    response_model=schemas.ResultModel,
    summary="Get current user info",
    description="Get information about the currently authenticated user"
)
async def read_users_me(
    current_user: models.User = Security(get_current_user, scopes=["user"])
) -> Dict[str, Any]:
    """
    Get the current user's information.
    """
    user_data = {
        "user_id": current_user.user_id,
        "user_name": current_user.user_name,
        "user_num": current_user.user_num,
        "user_role": current_user.user_role,
        "userrole_id": current_user.userrole_id,
        "tenant_id": int(current_user.tenant_id),
        "email": current_user.email,
        "phone": current_user.phone,
        "is_active": current_user.is_active,
        "create_time": current_user.create_time.isoformat() if current_user.create_time else None,
        "last_update_time": current_user.last_update_time.isoformat() if current_user.last_update_time else None
    }
    return schemas.result_success(user_data)

@router.post(
    "/change-password",
    response_model=schemas.ResultModel,
    summary="Change user password",
    description="Change the current user's password"
)
async def change_password(
    current_password: str,
    new_password: str,
    current_user: models.User = Security(get_current_user, scopes=["user"]),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Change the current user's password.
    """
    # Verify current password
    if not verify_password(md5_hex(current_password) if len(current_password) != 32 else current_password, current_user.password):
        return schemas.result_error("Current password is incorrect", status.HTTP_400_BAD_REQUEST)
    
    # Update password (hash the new password)
    current_user.password = get_password_hash(new_password if len(new_password) == 32 else md5_hex(new_password))
    db.add(current_user)
    db.commit()
    
    # Invalidate all user sessions
    cache.delete_token(current_user.user_id)
    
    return schemas.result_success("Password updated successfully")
