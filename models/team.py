# models/team.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    sport = Column(String(10), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    abbreviation = Column(String(10), nullable=False)
    conference = Column(String(50), nullable=True)
    division = Column(String(50), nullable=True)
    city = Column(String(50), nullable=True)
    state = Column(String(20), nullable=True)
    stadium = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    stats = relationship("TeamStats", back_populates="team", cascade="all, delete-orphan", lazy="select")
    
    def to_dict(self):
        """Convert team to dictionary for JSON responses"""
        return {
            'id': self.id,
            'sport': self.sport,
            'name': self.name,
            'abbreviation': self.abbreviation,
            'conference': self.conference,
            'division': self.division,
            'city': self.city,
            'state': self.state,
            'stadium': self.stadium,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}', abbr='{self.abbreviation}')>"

class TeamStats(Base):
    __tablename__ = "team_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=False)
    season_type = Column(String(20), default="regular")
    stats = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    team = relationship("Team", back_populates="stats")
    
    def to_dict(self):
        """Convert team stats to dictionary for JSON responses"""
        return {
            'id': self.id,
            'team_id': self.team_id,
            'year': self.year,
            'season_type': self.season_type,
            'stats': self.stats,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }