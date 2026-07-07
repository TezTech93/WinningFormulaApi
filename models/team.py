# models/team.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON,Enum
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
    
    # Relationships
    stats = relationship("TeamStats", back_populates="team", cascade="all, delete-orphan")
    gamelines = relationship("Gameline", back_populates="team")

class TeamStats(Base):
    __tablename__ = "team_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=False)
    season_type = Column(String(20), default="regular")
    stats = Column(JSON, nullable=False)  # Store all stats as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    team = relationship("Team", back_populates="stats")