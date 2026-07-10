# models/season_phase.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base

class SeasonPhase(Base):
    __tablename__ = "season_phases"
    
    id = Column(Integer, primary_key=True, index=True)
    sport = Column(String(10), nullable=False, unique=True, index=True)
    phase = Column(String(20), nullable=False)
    season = Column(String(20), nullable=False)
    week = Column(Integer, default=0)
    details = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'sport': self.sport,
            'phase': self.phase,
            'season': self.season,
            'week': self.week,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }