# managers/user_manager.py
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from core.security import hash_password, verify_password
from models.user import User, UserTier
from core.config import settings

class UserManager:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()
    
    def create_user(self, username: str, email: str, password: str) -> User:
        password_hash = hash_password(password)
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            tier=UserTier.FREE
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
    
    def update_user_tier(self, user_id: int, tier: str) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        user.tier = tier
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_user_tier_limit(self, user_id: int) -> int:
        user = self.get_user_by_id(user_id)
        if not user:
            return 0
        return settings.TIER_LIMITS.get(user.tier.value, 50)
    
    def get_formula_count(self, user_id: int) -> int:
        from models.formula import UserFormula
        return self.db.query(UserFormula).filter(UserFormula.user_id == user_id).count()
    
    def can_add_formula(self, user_id: int) -> bool:
        count = self.get_formula_count(user_id)
        limit = self.get_user_tier_limit(user_id)
        return count < limit