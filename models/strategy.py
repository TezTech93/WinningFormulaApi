# models/strategy.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from core.database import Base

class StrategyType(str, enum.Enum):
    BANKROLL = "bankroll"
    RESEARCH = "research"
    PSYCHOLOGY = "psychology"
    VALUE = "value"
    HEDGING = "hedging"

class UserStrategy(Base):
    __tablename__ = "user_strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    strategy_name = Column(String(100), nullable=False)
    strategy_type = Column(Enum(StrategyType), default=StrategyType.BANKROLL)
    description = Column(Text, nullable=True)
    target_amount = Column(Float, nullable=True)
    bankroll = Column(Float, nullable=True)
    unit_size = Column(Float, nullable=True)
    risk_percentage = Column(Float, default=3.0)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", backref="strategies")

class StrategyTip(Base):
    __tablename__ = "strategy_tips"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String(20), default="Beginner")  # Beginner, Intermediate, Advanced
    icon = Column(String(10), nullable=True)
    order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())