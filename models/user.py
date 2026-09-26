# models/user.py
from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean
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

    # Legacy tier — kept for backwards compat with user_manager
    tier = Column(Enum(UserTier), default=UserTier.FREE)

    # Superuser — exactly one user should have this True, set via SUPERUSER_EMAIL
    is_superuser = Column(Boolean, default=False, nullable=False)

    # --- Subscription (source of truth for gating) ---
    stripe_customer_id = Column(String, nullable=True, unique=True, index=True)
    stripe_subscription_id = Column(String, nullable=True, unique=True)
    subscription_status = Column(String(20), default="free", nullable=False)
    # free | active | past_due | canceled
    subscription_tier = Column(String(20), default="free", nullable=False)
    # free | standard | plus
    subscription_source = Column(String(20), default="none", nullable=False)
    # none | stripe | access_code | superuser
    subscription_current_period_end = Column(DateTime(timezone=True), nullable=True)

    # --- Timestamps (single definition now) ---
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    formulas = relationship("UserFormula", back_populates="user", cascade="all, delete-orphan", lazy="select")
    strategies = relationship("UserStrategy", back_populates="user", cascade="all, delete-orphan", lazy="select")
    predictions = relationship("UserPrediction", back_populates="user", cascade="all, delete-orphan", lazy="select")
    parlays = relationship("Parlay", back_populates="user", cascade="all, delete-orphan", lazy="select")