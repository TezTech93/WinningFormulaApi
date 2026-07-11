# models/gameline.py
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, TIMESTAMP
from sqlalchemy.sql import func
from datetime import datetime

from core.database import Base

class Gameline(Base):
    __tablename__ = "gamelines"
    
    id = Column(Integer, primary_key=True, index=True)
    sport = Column(String(10), nullable=False, index=True)
    source = Column(String(50), nullable=False)
    game_id = Column(String(50), nullable=False, unique=True, index=True)
    game_date = Column(TIMESTAMP, nullable=False, index=True)  # TIMESTAMP, not Date
    start_time = Column(String(20), nullable=True)
    
    # Your database uses INTEGER for team IDs
    home_team_id = Column(Integer, nullable=False)
    away_team_id = Column(Integer, nullable=False)
    home_abbr = Column(String(10), nullable=False)
    away_abbr = Column(String(10), nullable=False)
    
    home_ml = Column(Integer, nullable=True)
    away_ml = Column(Integer, nullable=True)
    home_spread = Column(Float, nullable=True)
    away_spread = Column(Float, nullable=True)
    home_spread_odds = Column(Integer, nullable=True)
    away_spread_odds = Column(Integer, nullable=True)
    total = Column(Float, nullable=True)  # Your schema uses 'total'
    over_odds = Column(Integer, nullable=True)
    under_odds = Column(Integer, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=True)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'sport': self.sport,
            'source': self.source,
            'game_id': self.game_id,
            'game_date': self.game_date.isoformat() if self.game_date else None,
            'start_time': self.start_time,
            'home_team_id': self.home_team_id,
            'away_team_id': self.away_team_id,
            'home_abbr': self.home_abbr,
            'away_abbr': self.away_abbr,
            'home_ml': self.home_ml,
            'away_ml': self.away_ml,
            'home_spread': self.home_spread,
            'away_spread': self.away_spread,
            'home_spread_odds': self.home_spread_odds,
            'away_spread_odds': self.away_spread_odds,
            'total': self.total,
            'over_odds': self.over_odds,
            'under_odds': self.under_odds,
            'is_completed': self.is_completed,
            'home_score': self.home_score,
            'away_score': self.away_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }