# managers/gameline_manager.py
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from models.gameline import Gameline
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class GamelineManager:
    def __init__(self, db: Session):
        self.db = db
    
    def create_gameline(self, data: Dict[str, Any]) -> Gameline:
        gameline = Gameline(
            sport=data.get('sport'),
            source=data.get('source', 'espn_bets'),
            game_id=data.get('game_id'),
            home_team=data.get('home_team'),
            away_team=data.get('away_team'),
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
            start_time=data.get('start_time')
        )
        self.db.add(gameline)
        self.db.commit()
        self.db.refresh(gameline)
        return gameline
    
    def get_gamelines_by_sport(self, sport: str, source: str = None) -> List[Gameline]:
        query = self.db.query(Gameline).filter(Gameline.sport == sport)
        if source:
            query = query.filter(Gameline.source == source)
        return query.filter(Gameline.game_date >= datetime.now()).order_by(Gameline.game_date).all()
    
    def get_gamelines_by_game(self, game_id: str) -> Optional[Gameline]:
        return self.db.query(Gameline).filter(Gameline.game_id == game_id).first()
    
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
    
    def delete_old_gamelines(self, days: int = 7) -> int:
        """Delete gamelines older than specified days"""
        cutoff = datetime.now() - timedelta(days=days)
        deleted = self.db.query(Gameline).filter(
            Gameline.game_date < cutoff
        ).delete()
        self.db.commit()
        return deleted