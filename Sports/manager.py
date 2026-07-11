# sports/manager.py
import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import json

from core.database import get_db
from models.gamelines import Gameline
from models.season_phase import SeasonPhase
from Sports.base_scraper import BaseSportScraper
from Sports.nfl.scraper import NFLScraper
from Sports.nba.scraper import NBAScraper
from Sports.mlb.scraper import MLBScraper
from Sports.nhl.scraper import NHLScraper
from Sports.ncaaf.scraper import NCAAFScraper
from Sports.ncaab.scraper import NCAABScraper

logger = logging.getLogger(__name__)

class SportsManager:
    """Unified manager for all sports with PostgreSQL support"""
    
    SUPPORTED_SPORTS = ['nfl', 'nba', 'mlb', 'nhl', 'ncaaf', 'ncaab']
    
    def __init__(self):
        self.scrapers = {}
        self._init_scrapers()
    
    def _init_scrapers(self):
        """Initialize all sport scrapers"""
        self.scrapers = {
            'nfl': NFLScraper(),
            'nba': NBAScraper(),
            'mlb': MLBScraper(),
            'nhl': NHLScraper(),
            'ncaaf': NCAAFScraper(),
            'ncaab': NCAABScraper()
        }
        logger.info(f"Initialized scrapers for {list(self.scrapers.keys())}")
    
    def get_scraper(self, sport: str) -> Optional[BaseSportScraper]:
        """Get scraper for a specific sport"""
        return self.scrapers.get(sport)
    
    def _get_cached_gamelines(self, db: Session, sport: str) -> List[Dict]:
        """Get cached gamelines from PostgreSQL database"""
        try:
            gamelines = db.query(Gameline).filter(
                Gameline.sport == sport,
                Gameline.is_completed == False
            ).order_by(Gameline.game_date).all()
            
            return [g.to_dict() for g in gamelines]
        except Exception as e:
            logger.error(f"Error reading cached gamelines: {e}")
            return []
    
    def _store_gamelines(self, db: Session, sport: str, games: List[Dict], source: str = 'web_scraper'):
    """Store gamelines in PostgreSQL database"""
        try:
            for game in games:
                # Check if game already exists
                existing = db.query(Gameline).filter(
                    Gameline.game_id == game.get('game_id')
                ).first()
                
                if existing:
                    # Update existing - only update fields that exist
                    for key, value in game.items():
                        # Skip keys that aren't in the model
                        if hasattr(existing, key) and value is not None:
                            setattr(existing, key, value)
                    existing.updated_at = datetime.now()
                else:
                    # Create new - match your database schema exactly
                    new_gameline = Gameline(
                        sport=sport,
                        source=source,
                        game_id=game.get('game_id', f"{sport}_{int(datetime.now().timestamp())}"),
                        game_date=datetime.strptime(game.get('game_date'), '%Y-%m-%d'),
                        start_time=game.get('start_time'),
                        home_team_id=int(game.get('home_team_id') or game.get('home', 0)),
                        away_team_id=int(game.get('away_team_id') or game.get('away', 0)),
                        home_abbr=game.get('home_abbr') or game.get('home', '')[:3].upper(),
                        away_abbr=game.get('away_abbr') or game.get('away', '')[:3].upper(),
                        home_ml=game.get('home_ml'),
                        away_ml=game.get('away_ml'),
                        home_spread=game.get('home_spread'),
                        away_spread=game.get('away_spread'),
                        home_spread_odds=game.get('home_spread_odds', -110),
                        away_spread_odds=game.get('away_spread_odds', -110),
                        total=game.get('total'),
                        over_odds=game.get('over_odds', -110),
                        under_odds=game.get('under_odds', -110),
                        is_completed=game.get('is_completed', False),
                        home_score=game.get('home_score'),
                        away_score=game.get('away_score')
                    )
                    db.add(new_gameline)
            
            db.commit()
            logger.info(f"Stored {len(games)} games for {sport}")
        except Exception as e:
            logger.error(f"Error storing gamelines: {e}")
            db.rollback()

    def _store_single_gameline(self, db: Session, sport: str, game: Dict) -> bool:
        """Store a single gameline in PostgreSQL database"""
        try:
            game_id = game.get('game_id', f"{sport}_manual_{int(datetime.now().timestamp())}")
            existing = db.query(Gameline).filter(
                Gameline.game_id == game_id
            ).first()
            
            if existing:
                for key, value in game.items():
                    if hasattr(existing, key) and value is not None:
                        setattr(existing, key, value)
                existing.updated_at = datetime.now()
            else:
                new_gameline = Gameline(
                    sport=sport,
                    source='manual',
                    game_id=game_id,
                    game_date=datetime.strptime(game.get('game_date'), '%Y-%m-%d'),
                    start_time=game.get('start_time'),
                    home_team_id=int(game.get('home_team_id')),  # Convert to int
                    away_team_id=int(game.get('away_team_id')),  # Convert to int
                    home_abbr=game.get('home_abbr'),
                    away_abbr=game.get('away_abbr'),
                    home_ml=game.get('home_ml'),
                    away_ml=game.get('away_ml'),
                    home_spread=game.get('home_spread'),
                    away_spread=game.get('away_spread'),
                    home_spread_odds=game.get('home_spread_odds'),
                    away_spread_odds=game.get('away_spread_odds'),
                    total=game.get('total'),
                    over_odds=game.get('over_odds'),
                    under_odds=game.get('under_odds'),
                    is_completed=game.get('is_completed', False)
                )
                db.add(new_gameline)
            
            db.commit()
            logger.info(f"Stored gameline: {game.get('home_team_id')} vs {game.get('away_team_id')}")
            return True
        except Exception as e:
            logger.error(f"Error storing manual gameline: {e}")
            db.rollback()
            return False
    
    def _store_season_phase(self, db: Session, sport: str, phase: Dict):
        """Store season phase in PostgreSQL database"""
        try:
            existing = db.query(SeasonPhase).filter(
                SeasonPhase.sport == sport
            ).first()
            
            if existing:
                existing.phase = phase.get('phase')
                existing.season = phase.get('season')
                existing.week = phase.get('week', 0)
                existing.details = phase.get('details')
                existing.updated_at = datetime.now()
            else:
                new_phase = SeasonPhase(
                    sport=sport,
                    phase=phase.get('phase'),
                    season=phase.get('season'),
                    week=phase.get('week', 0),
                    details=phase.get('details')
                )
                db.add(new_phase)
            
            db.commit()
        except Exception as e:
            logger.error(f"Error storing season phase: {e}")
            db.rollback()
    
    async def get_gamelines(self, sport: str, db: Session, force_refresh: bool = False) -> Dict[str, Any]:
        """Get gamelines for a specific sport"""
        if sport not in self.SUPPORTED_SPORTS:
            return {'error': f'Unsupported sport: {sport}', 'games': [], 'count': 0}
        
        scraper = self.get_scraper(sport)
        if not scraper:
            return {'error': f'No scraper found for {sport}', 'games': [], 'count': 0}
        
        # Try to get cached data first
        if not force_refresh:
            cached = self._get_cached_gamelines(db, sport)
            if cached:
                return {
                    'sport': sport,
                    'source': 'cached',
                    'games': cached,
                    'count': len(cached),
                    'cached': True
                }
        
        # Fetch fresh data
        games = scraper.get_gamelines()
        if games:
            self._store_gamelines(db, sport, games, source='web_scraper')
        
        return {
            'sport': sport,
            'source': 'live',
            'games': games,
            'count': len(games),
            'cached': False
        }
    
    async def get_team_stats(self, sport: str, team: str, year: str) -> Dict[str, Any]:
        """Get team stats for a specific sport"""
        if sport not in self.SUPPORTED_SPORTS:
            return {'error': f'Unsupported sport: {sport}', 'stats': []}
        
        scraper = self.get_scraper(sport)
        if not scraper:
            return {'error': f'No scraper found for {sport}', 'stats': []}
        
        stats = scraper.get_team_stats(team, year)
        return {
            'sport': sport,
            'team': team,
            'year': year,
            'stats': stats,
            'count': len(stats)
        }
    
    async def get_season_phase(self, sport: str, db: Session) -> Dict[str, Any]:
        """Get current season phase for a sport"""
        if sport not in self.SUPPORTED_SPORTS:
            return {'error': f'Unsupported sport: {sport}'}
        
        scraper = self.get_scraper(sport)
        if not scraper:
            return {'error': f'No scraper found for {sport}'}
        
        phase = scraper.get_season_phase()
        self._store_season_phase(db, sport, phase)
        return phase
    
    def manual_add_gameline(self, sport: str, db: Session, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a single gameline manually"""
        if sport not in self.SUPPORTED_SPORTS:
            return {'error': f'Unsupported sport: {sport}'}
        
        # Validate required fields
        required = ['home_team', 'away_team', 'game_date']
        for field in required:
            if field not in game_data or not game_data[field]:
                return {'error': f'Missing required field: {field}'}
        
        # Generate game_id if not provided
        if 'game_id' not in game_data:
            game_data['game_id'] = f"{sport}_manual_{int(datetime.now().timestamp())}"
        
        # Set defaults
        game_data['sport'] = sport
        game_data['source'] = 'manual'
        game_data['is_manual'] = True
        
        # Add abbreviations if not provided
        if 'home_abbr' not in game_data or not game_data['home_abbr']:
            scraper = self.get_scraper(sport)
            if scraper:
                game_data['home_abbr'] = scraper.get_team_abbr(game_data['home_team'])
                game_data['away_abbr'] = scraper.get_team_abbr(game_data['away_team'])
        
        # Store in database
        success = self._store_single_gameline(db, sport, game_data)
        
        if success:
            return {
                'message': 'Gameline added successfully',
                'game': game_data
            }
        else:
            return {'error': 'Failed to add gameline'}
    
    def manual_add_gamelines_bulk(self, sport: str, db: Session, games_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add multiple gamelines manually from JSON data"""
        if sport not in self.SUPPORTED_SPORTS:
            return {'error': f'Unsupported sport: {sport}'}
        
        if not games_data or not isinstance(games_data, list):
            return {'error': 'Invalid data format. Expected array of games'}
        
        added = 0
        errors = []
        
        for i, game_data in enumerate(games_data):
            result = self.manual_add_gameline(sport, db, game_data)
            if 'error' in result:
                errors.append({'index': i, 'error': result['error']})
            else:
                added += 1
        
        return {
            'message': f'Added {added} gamelines',
            'added': added,
            'errors': errors,
            'total': len(games_data)
        }

# Create singleton instance
sports_manager = SportsManager()