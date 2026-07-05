# models/parlay.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from core.database import Base

class ParlayStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    WON = "won"
    LOST = "lost"
    CANCELLED = "cancelled"

class Parlay(Base):
    __tablename__ = "parlays"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    sport = Column(String(10), nullable=False)
    name = Column(String(100), nullable=True)
    bet_amount = Column(Float, nullable=False, default=10.0)
    total_odds = Column(Float, nullable=False, default=0.0)
    potential_payout = Column(Float, nullable=False, default=0.0)
    potential_profit = Column(Float, nullable=False, default=0.0)
    status = Column(Enum(ParlayStatus), default=ParlayStatus.PENDING)
    selections_count = Column(Integer, nullable=False, default=0)
    metadata = Column(JSON, nullable=True)  # Store additional data like locks, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="parlays")
    selections = relationship("ParlaySelection", back_populates="parlay", cascade="all, delete-orphan")

class ParlaySelection(Base):
    __tablename__ = "parlay_selections"
    
    id = Column(Integer, primary_key=True, index=True)
    parlay_id = Column(Integer, ForeignKey("parlays.id", ondelete="CASCADE"), nullable=False)
    game_id = Column(String(50), nullable=False)
    selection_type = Column(String(20), nullable=False)  # spread, moneyline, overunder
    selection_value = Column(String(50), nullable=False)  # The actual selection (e.g., "DET -3.5")
    odds = Column(Float, nullable=False)
    is_locked = Column(Integer, default=0)  # 0 = not locked, 1 = win lock, 2 = loss lock
    result = Column(String(10), nullable=True)  # W, L, P (push)
    order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    parlay = relationship("Parlay", back_populates="selections")