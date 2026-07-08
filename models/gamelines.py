# models/gameline.py
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base

class Gameline(Base):
    __tablename__ = "gamelines"
    
    id = Column(Integer, primary_key=True, index=True)
    sport = Column(String(10), nullable=False, index=True)
    source = Column(String(50), nullable=False)
    game_id = Column(String(50), nullable=False, index=True)
    
    # Use home_team_id and away_team_id to match your DB schema
    home_team_id = Column(Integer, nullable=True)  # Foreign key to teams table
    away_team_id = Column(Integer, nullable=True)  # Foreign key to teams table
    
    # Keep these for backward compatibility
    home_team = Column(String(100), nullable=True)
    away_team = Column(String(100), nullable=True)
    home_abbr = Column(String(10), nullable=True)
    away_abbr = Column(String(10), nullable=True)
    
    home_ml = Column(Integer, nullable=True)
    away_ml = Column(Integer, nullable=True)
    home_spread = Column(Float, nullable=True)
    away_spread = Column(Float, nullable=True)
    home_spread_odds = Column(Integer, nullable=True)
    away_spread_odds = Column(Integer, nullable=True)
    total = Column(Float, nullable=True)
    over_odds = Column(Integer, nullable=True)
    under_odds = Column(Integer, nullable=True)
    game_date = Column(DateTime, nullable=False, index=True)
    start_time = Column(String(20), nullable=True)
    is_completed = Column(Boolean, default=False)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_gamelines_sport_date', 'sport', 'game_date'),
        Index('idx_gamelines_completed', 'is_completed'),
    )