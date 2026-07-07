# models/predictions.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from core.database import Base

class PredictionType(str, enum.Enum):
    HOME = "home"
    AWAY = "away"
    OVER = "over"
    UNDER = "under"
    SPREAD_HOME = "spread_home"
    SPREAD_AWAY = "spread_away"

class UserPrediction(Base):
    __tablename__ = "user_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    game_id = Column(String(50), nullable=False)
    sport = Column(String(10), nullable=False)
    home_team = Column(String(100), nullable=False)
    away_team = Column(String(100), nullable=False)
    home_abbr = Column(String(10), nullable=False)
    away_abbr = Column(String(10), nullable=False)
    prediction_type = Column(Enum(PredictionType), nullable=False)
    predicted_value = Column(Float, nullable=True)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    status = Column(String(20), default="upcoming")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="predictions")