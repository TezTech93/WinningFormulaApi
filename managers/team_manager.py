# managers/team_manager.py
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from models.team import Team
import logging

logger = logging.getLogger(__name__)

class TeamManager:
    def __init__(self, db: Session):
        self.db = db
    
    def create_team(self, data: Dict[str, Any]) -> Team:
        """Create a new team"""
        team = Team(
            sport=data.get('sport'),
            name=data.get('name'),
            abbreviation=data.get('abbreviation'),
            conference=data.get('conference'),
            division=data.get('division'),
            city=data.get('city'),
            state=data.get('state'),
            stadium=data.get('stadium')
        )
        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)
        return team
    
    def get_team_by_id(self, team_id: int) -> Optional[Team]:
        return self.db.query(Team).filter(Team.id == team_id).first()
    
    def get_team_by_abbr(self, sport: str, abbr: str) -> Optional[Team]:
        return self.db.query(Team).filter(
            Team.sport == sport,
            Team.abbreviation == abbr
        ).first()
    
    def get_teams_by_sport(self, sport: str) -> List[Team]:
        return self.db.query(Team).filter(Team.sport == sport).order_by(Team.name).all()
    
    def get_teams_by_conference(self, sport: str, conference: str) -> List[Team]:
        return self.db.query(Team).filter(
            Team.sport == sport,
            Team.conference == conference
        ).order_by(Team.name).all()
    
    def update_team(self, team_id: int, data: Dict[str, Any]) -> Optional[Team]:
        team = self.get_team_by_id(team_id)
        if team:
            for key, value in data.items():
                if hasattr(team, key) and value is not None:
                    setattr(team, key, value)
            team.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(team)
            return team
        return None
    
    def upsert_team(self, data: Dict[str, Any]) -> Team:
        """Update or create a team"""
        existing = self.db.query(Team).filter(
            Team.sport == data.get('sport'),
            Team.abbreviation == data.get('abbreviation')
        ).first()
        
        if existing:
            # Update existing
            for key, value in data.items():
                if hasattr(existing, key) and value is not None:
                    setattr(existing, key, value)
            existing.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            return self.create_team(data)