# models/user.py
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from core.database import Base

class UserTier(str, enum.Enum):
    FREE = "FREE"
    PAID = "PAID"
    PLUS = "PLUS"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    tier = Column(Enum(UserTier), default=UserTier.FREE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships - using string references to avoid circular imports
    formulas = relationship("UserFormula", back_populates="user", cascade="all, delete-orphan", lazy="select")
    strategies = relationship("UserStrategy", back_populates="user", cascade="all, delete-orphan", lazy="select")
    predictions = relationship("UserPrediction", back_populates="user", cascade="all, delete-orphan", lazy="select")
    parlays = relationship("Parlay", back_populates="user", cascade="all, delete-orphan", lazy="select")