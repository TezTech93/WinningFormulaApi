# routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from core.database import get_db
from core.dependencies import get_current_user, get_current_user_with_tier
from managers.user_manager import UserManager
from models.user import User

router = APIRouter(prefix="/users", tags=["Users"])

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)

class TierUpdate(BaseModel):
    tier: str = Field(..., pattern="^(FREE|PAID|PLUS)$")

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    tier: str
    created_at: str

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "tier": current_user.tier.value,
        "created_at": current_user.created_at.isoformat()
    }

@router.put("/me/password")
async def update_password(
    password_data: PasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user password"""
    user_manager = UserManager(db)
    
    # Verify current password
    if not user_manager.authenticate_user(current_user.email, password_data.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    from core.security import hash_password
    user = user_manager.get_user_by_id(current_user.id)
    user.password_hash = hash_password(password_data.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}

@router.get("/me/tier")
async def get_my_tier(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's tier information"""
    user_manager = UserManager(db)
    limit = user_manager.get_user_tier_limit(current_user.id)
    count = user_manager.get_formula_count(current_user.id)
    
    return {
        "tier": current_user.tier.value,
        "limit": limit,
        "used": count,
        "remaining": limit - count
    }

@router.put("/{user_id}/tier")
async def update_user_tier(
    user_id: int,
    tier_data: TierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_tier("PLUS"))
):
    """Update user tier (Admin only - requires PLUS tier)"""
    user_manager = UserManager(db)
    user = user_manager.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    updated_user = user_manager.update_user_tier(user_id, tier_data.tier)
    
    return {
        "message": f"User tier updated to {tier_data.tier}",
        "user": {
            "id": updated_user.id,
            "username": updated_user.username,
            "email": updated_user.email,
            "tier": updated_user.tier.value
        }
    }