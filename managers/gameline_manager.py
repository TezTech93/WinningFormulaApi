# managers/gameline_manager.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from models.gamelines import Gameline
from models.team import Team

logger = logging.getLogger(__name__)

class GamelineManager:
    def __init__(self, db: Session):
        self.db = db
    
    def create_gameline(self, data: Dict[str, Any]) -> Gameline:
        """Create a new gameline"""
        gameline = Gameline(
            sport=data.get('sport'),
            source=data.get('source', 'espn_bets'),
            game_id=data.get('game_id'),
            home_team_id=data.get('home_team_id'),
            away_team_id=data.get('away_team_id'),
            home_abbr=data.get('home_abbr'),
            away_abbr=data.get('away_abbr'),
            home_ml=data.get('home_ml'),
            away_ml=data.get('away_ml'),
            home_spread=data.get('home_spread'),
            away_spread=data.get('away_spread'),
            home_spread_odds=data.get('home_spread_odds'),
            away_spread_odds=data.get('away_spread_odds'),
            total=data.get('total'),
            over_odds=data.get('over_odds'),
            under_odds=data.get('under_odds'),
            game_date=data.get('game_date'),
            start_time=data.get('start_time'),
        )
        self.db.add(gameline)
        self.db.commit()
        self.db.refresh(gameline)
        return gameline
    
    def upsert_gameline(self, data: Dict[str, Any]) -> Gameline:
        """Update or insert a gameline"""
        existing = self.db.query(Gameline).filter(
            Gameline.game_id == data.get('game_id'),
            Gameline.source == data.get('source', 'espn_bets')
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
            return self.create_gameline(data)
    
    def get_gamelines_by_sport(self, sport: str, source: str = None) -> List[Gameline]:
        """Get upcoming gamelines for a sport"""
        query = self.db.query(Gameline).filter(
            Gameline.sport == sport,
            Gameline.is_completed == False,
            Gameline.game_date >= datetime.now() - timedelta(hours=1)
        )
        if source:
            query = query.filter(Gameline.source == source)
        return query.order_by(Gameline.game_date).all()
    
    def get_gamelines_by_team(self, team_id: int, num_games: int = 10) -> List[Gameline]:
        """Get upcoming gamelines for a team"""
        return self.db.query(Gameline).filter(
            or_(
                Gameline.home_team_id == team_id,
                Gameline.away_team_id == team_id
            ),
            Gameline.is_completed == False,
            Gameline.game_date >= datetime.now() - timedelta(hours=1)
        ).order_by(Gameline.game_date).limit(num_games).all()
    
    def mark_completed_games(self) -> int:
        """Mark games as completed if they've started"""
        now = datetime.now()
        games = self.db.query(Gameline).filter(
            Gameline.is_completed == False,
            Gameline.game_date < now
        ).all()
        
        for game in games:
            game.is_completed = True
        
        self.db.commit()
        count = len(games)
        if count > 0:
            logger.info(f"Marked {count} games as completed")
        return count
    
    def delete_old_gamelines(self, days: int = 7) -> int:
        """Delete gamelines older than specified days that are completed"""
        cutoff = datetime.now() - timedelta(days=days)
        deleted = self.db.query(Gameline).filter(
            Gameline.is_completed == True,
            Gameline.game_date < cutoff
        ).delete()
        self.db.commit()
        if deleted > 0:
            logger.info(f"Deleted {deleted} old gamelines")
        return deleted
    
    def update_game_score(self, game_id: str, home_score: int, away_score: int) -> Optional[Gameline]:
        """Update a game with final scores"""
        game = self.db.query(Gameline).filter(Gameline.game_id == game_id).first()
        if game:
            game.home_score = home_score
            game.away_score = away_score
            game.is_completed = True
            game.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(game)
            return game
        return None
    
    def get_recent_games_for_team(self, team_id: int, num_games: int = 5) -> List[Gameline]:
        """Get a team's recent completed games"""
        return self.db.query(Gameline).filter(
            or_(
                Gameline.home_team_id == team_id,
                Gameline.away_team_id == team_id
            ),
            Gameline.is_completed == True
        ).order_by(Gameline.game_date.desc()).limit(num_games).all()