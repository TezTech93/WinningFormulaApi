# core/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from jose import jwt, JWTError

from core.database import get_db
from core.config import settings
from core.security import decode_access_token
from models.user import User
from managers.user_manager import UserManager

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token
    """
    token = credentials.credentials
    
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_manager = UserManager(db)
    user = user_manager.get_user_by_id(int(user_id))
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user (could add additional checks here)
    """
    # Add any additional checks here (e.g., email verified, account active, etc.)
    return current_user

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get the current user if authenticated, otherwise return None
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    
    user_manager = UserManager(db)
    user = user_manager.get_user_by_id(int(user_id))
    return user

def get_current_user_with_tier(required_tier: str = None):
    """
    Dependency factory for checking user tier
    """
    async def _get_current_user_with_tier(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if required_tier:
            tier_priority = {
                "FREE": 0,
                "PAID": 1,
                "PLUS": 2
            }
            
            user_tier_priority = tier_priority.get(current_user.tier.value, 0)
            required_tier_priority = tier_priority.get(required_tier, 0)
            
            if user_tier_priority < required_tier_priority:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires {required_tier} tier or higher. Current tier: {current_user.tier.value}"
                )
        
        return current_user
    
    return _get_current_user_with_tier

# Convenience dependencies for different tier levels
get_free_user = get_current_user_with_tier("FREE")
get_paid_user = get_current_user_with_tier("PAID")
get_plus_user = get_current_user_with_tier("PLUS")