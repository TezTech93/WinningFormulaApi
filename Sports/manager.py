# sports/manager.py
import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import json

from core.database import get_db
from models.gamelines import Gameline
from models.team import Team
from models.season_phase import SeasonPhase
from Sports.base_scraper import BaseSportScraper
from Sports.nfl.scraper import NFLScraper
from Sports.nba.scraper import NBAScraper
from Sports.mlb.scraper import MLBScraper
from Sports.nhl.scraper import NHLScraper
from Sports.ncaaf.scraper import NCAAFScraper
from Sports.ncaab.scraper import NCAABScraper

# Import team data
from Sports.nfl.nfl_teams import nfl_teams
from Sports.nba.nba_teams import nba_teams
from Sports.mlb.mlb_teams import mlb_teams
from Sports.nhl.nhl_teams import nhl_teams

logger = logging.getLogger(__name__)

class SportsManager:
    """Unified manager for all sports with PostgreSQL support"""
    
    SUPPORTED_SPORTS = ['nfl', 'nba', 'mlb', 'nhl', 'ncaaf', 'ncaab']
    
    # Team data mappings
    TEAM_DATA = {
        'nfl': nfl_teams,
        'nba': nba_teams,
        'mlb': mlb_teams,
        'nhl': nhl_teams,
        # 'ncaaf': ncaaf_teams,  # Add when available
        # 'ncaab': ncaab_teams,  # Add when available
    }
    
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
    
    # ==================== TEAM MANAGEMENT ====================
    
    def get_teams(self, sport: str, db: Session) -> Dict[str, Any]:
        """Get all teams for a sport from database or fallback to hardcoded data"""
        if sport not in self.SUPPORTED_SPORTS:
            return {'error': f'Unsupported sport: {sport}', 'teams': [], 'count': 0}
        
        try:
            # Try to get teams from database first
            teams = db.query(Team).filter(Team.sport == sport).order_by(Team.name).all()
            
            if teams:
                return {
                    'sport': sport,
                    'source': 'database',
                    'teams': [team.to_dict() for team in teams],
                    'count': len(teams)
                }
        except Exception as e:
            logger.warning(f"Could not fetch teams from database: {e}")
        
        # Fallback to hardcoded team data
        teams_data = self.TEAM_DATA.get(sport, [])
        formatted_teams = []
        
        for idx, team in enumerate(teams_data, start=1):
            formatted_teams.append({
                'id': idx,
                'sport': sport,
                'name': f"{team['city']} {team['teamName']}",
                'abbreviation': team['abv'].upper(),
                'conference': None,
                'division': None,
                'city': team['city'],
            })
        
        return {
            'sport': sport,
            'source': 'hardcoded',
            'teams': formatted_teams,
            'count': len(formatted_teams)
        }
    
    def get_team_by_id(self, sport: str, team_id: int, db: Session) -> Optional[Dict]:
        """Get a specific team by ID"""
        if sport not in self.SUPPORTED_SPORTS:
            return None
        
        try:
            # Try database first
            team = db.query(Team).filter(
                Team.sport == sport,
                Team.id == team_id
            ).first()
            
            if team:
                return team.to_dict()
        except Exception as e:
            logger.warning(f"Could not fetch team from database: {e}")
        
        # Fallback to hardcoded
        teams_data = self.TEAM_DATA.get(sport, [])
        if 1 <= team_id <= len(teams_data):
            team = teams_data[team_id - 1]
            return {
                'id': team_id,
                'sport': sport,
                'name': f"{team['city']} {team['teamName']}",
                'abbreviation': team['abv'].upper(),
                'conference': None,
                'division': None,
                'city': team['city'],
            }
        
        return None
    
    def get_team_by_abbr(self, sport: str, abbr: str, db: Session) -> Optional[Dict]:
        """Get a team by abbreviation"""
        if sport not in self.SUPPORTED_SPORTS:
            return None
        
        abbr = abbr.upper()
        
        try:
            # Try database first
            team = db.query(Team).filter(
                Team.sport == sport,
                Team.abbreviation == abbr
            ).first()
            
            if team:
                return team.to_dict()
        except Exception as e:
            logger.warning(f"Could not fetch team from database: {e}")
        
        # Fallback to hardcoded
        teams_data = self.TEAM_DATA.get(sport, [])
        for idx, team in enumerate(teams_data, start=1):
            if team['abv'].upper() == abbr:
                return {
                    'id': idx,
                    'sport': sport,
                    'name': f"{team['city']} {team['teamName']}",
                    'abbreviation': team['abv'].upper(),
                    'conference': None,
                    'division': None,
                    'city': team['city'],
                }
        
        return None
    
    def get_team_by_name(self, sport: str, name: str, db: Session) -> Optional[Dict]:
        """Get a team by full name (partial match)"""
        if sport not in self.SUPPORTED_SPORTS:
            return None
        
        try:
            # Try database first
            team = db.query(Team).filter(
                Team.sport == sport,
                Team.name.ilike(f"%{name}%")
            ).first()
            
            if team:
                return team.to_dict()
        except Exception as e:
            logger.warning(f"Could not fetch team from database: {e}")
        
        # Fallback to hardcoded
        teams_data = self.TEAM_DATA.get(sport, [])
        for idx, team in enumerate(teams_data, start=1):
            team_full_name = f"{team['city']} {team['teamName']}"
            if name.lower() in team_full_name.lower():
                return {
                    'id': idx,
                    'sport': sport,
                    'name': team_full_name,
                    'abbreviation': team['abv'].upper(),
                    'conference': None,
                    'division': None,
                    'city': team['city'],
                }
        
        return None
    
    def get_teams_by_conference(self, sport: str, conference: str, db: Session) -> Dict[str, Any]:
        """Get all teams in a specific conference"""
        if sport not in self.SUPPORTED_SPORTS:
            return {'error': f'Unsupported sport: {sport}', 'teams': [], 'count': 0}
        
        try:
            teams = db.query(Team).filter(
                Team.sport == sport,
                Team.conference == conference
            ).order_by(Team.name).all()
            
            return {
                'sport': sport,
                'conference': conference,
                'source': 'database',
                'teams': [team.to_dict() for team in teams],
                'count': len(teams)
            }
        except Exception as e:
            logger.error(f"Error fetching teams by conference: {e}")
            return {
                'sport': sport,
                'conference': conference,
                'source': 'error',
                'teams': [],
                'count': 0,
                'error': str(e)
            }
    
    def get_teams_by_division(self, sport: str, division: str, db: Session) -> Dict[str, Any]:
        """Get all teams in a specific division"""
        if sport not in self.SUPPORTED_SPORTS:
            return {'error': f'Unsupported sport: {sport}', 'teams': [], 'count': 0}
        
        try:
            teams = db.query(Team).filter(
                Team.sport == sport,
                Team.division == division
            ).order_by(Team.name).all()
            
            return {
                'sport': sport,
                'division': division,
                'source': 'database',
                'teams': [team.to_dict() for team in teams],
                'count': len(teams)
            }
        except Exception as e:
            logger.error(f"Error fetching teams by division: {e}")
            return {
                'sport': sport,
                'division': division,
                'source': 'error',
                'teams': [],
                'count': 0,
                'error': str(e)
            }
    
    def get_conferences(self, sport: str, db: Session) -> Dict[str, Any]:
        """Get all conferences for a sport"""
        if sport not in self.SUPPORTED_SPORTS:
            return {'error': f'Unsupported sport: {sport}', 'conferences': []}
        
        try:
            conferences = db.query(Team.conference).filter(
                Team.sport == sport,
                Team.conference.isnot(None)
            ).distinct().all()
            
            return {
                'sport': sport,
                'source': 'database',
                'conferences': [c[0] for c in conferences if c[0]]
            }
        except Exception as e:
            logger.error(f"Error fetching conferences: {e}")
            return {
                'sport': sport,
                'source': 'error',
                'conferences': [],
                'error': str(e)
            }
    
    def get_divisions(self, sport: str, db: Session) -> Dict[str, Any]:
        """Get all divisions for a sport"""
        if sport not in self.SUPPORTED_SPORTS:
            return {'error': f'Unsupported sport: {sport}', 'divisions': []}
        
        try:
            divisions = db.query(Team.division).filter(
                Team.sport == sport,
                Team.division.isnot(None)
            ).distinct().all()
            
            return {
                'sport': sport,
                'source': 'database',
                'divisions': [d[0] for d in divisions if d[0]]
            }
        except Exception as e:
            logger.error(f"Error fetching divisions: {e}")
            return {
                'sport': sport,
                'source': 'error',
                'divisions': [],
                'error': str(e)
            }
    
    def seed_teams(self, sport: str, db: Session) -> Dict[str, Any]:
        """Seed teams into the database from hardcoded data"""
        if sport not in self.SUPPORTED_SPORTS:
            return {'error': f'Unsupported sport: {sport}'}
        
        teams_data = self.TEAM_DATA.get(sport, [])
        if not teams_data:
            return {'error': f'No team data available for {sport}'}
        
        added = 0
        updated = 0
        
        for team_data in teams_data:
            team_name = f"{team_data['city']} {team_data['teamName']}"
            abbr = team_data['abv'].upper()
            
            try:
                # Check if team already exists
                existing = db.query(Team).filter(
                    Team.sport == sport,
                    Team.abbreviation == abbr
                ).first()
                
                if existing:
                    # Update existing
                    existing.name = team_name
                    existing.abbreviation = abbr
                    existing.city = team_data['city']
                    existing.updated_at = datetime.now()
                    updated += 1
                else:
                    # Create new team
                    team = Team(
                        sport=sport,
                        name=team_name,
                        abbreviation=abbr,
                        conference=None,
                        division=None,
                        city=team_data['city'],
                        state=None,
                        stadium=None
                    )
                    db.add(team)
                    added += 1
            except Exception as e:
                logger.error(f"Error seeding team {team_name}: {e}")
                db.rollback()
                return {
                    'error': f'Error seeding team {team_name}: {str(e)}',
                    'sport': sport,
                    'added': added,
                    'updated': updated
                }
        
        try:
            db.commit()
            logger.info(f"Seeded {added} teams, updated {updated} teams for {sport}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error committing teams: {e}")
            return {
                'error': f'Error committing teams: {str(e)}',
                'sport': sport,
                'added': added,
                'updated': updated
            }
        
        return {
            'message': f'Seeded {added} teams, updated {updated} teams for {sport}',
            'sport': sport,
            'added': added,
            'updated': updated,
            'total': len(teams_data)
        }
    
    def seed_all_teams(self, db: Session) -> Dict[str, Any]:
        """Seed all sports teams into the database"""
        results = {}
        for sport in self.SUPPORTED_SPORTS:
            if sport in self.TEAM_DATA:
                results[sport] = self.seed_teams(sport, db)
            else:
                results[sport] = {'error': f'No team data for {sport}'}
        
        return results
    
    def get_team_stats_by_team_id(self, sport: str, team_id: int, year: Optional[int] = None, db: Session = None) -> Dict[str, Any]:
        """Get team stats by team ID"""
        if sport not in self.SUPPORTED_SPORTS:
            return {'error': f'Unsupported sport: {sport}', 'stats': []}
        
        try:
            from models.team import TeamStats
            
            query = db.query(TeamStats).filter(
                TeamStats.team_id == team_id
            )
            
            if year:
                query = query.filter(TeamStats.year == year)
            
            stats = query.order_by(TeamStats.year.desc()).all()
            
            return {
                'sport': sport,
                'team_id': team_id,
                'stats': [stat.to_dict() for stat in stats],
                'count': len(stats)
            }
        except Exception as e:
            logger.error(f"Error fetching team stats: {e}")
            return {
                'sport': sport,
                'team_id': team_id,
                'stats': [],
                'count': 0,
                'error': str(e)
            }
    
    # ==================== GAMELINE MANAGEMENT ====================
    
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
                    home_team_id=int(game.get('home_team_id', 0)),
                    away_team_id=int(game.get('away_team_id', 0)),
                    home_abbr=game.get('home_abbr', '')[:3].upper(),
                    away_abbr=game.get('away_abbr', '')[:3].upper(),
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
        
        # Normalize field names - handle both naming conventions
        if 'home_team' in game_data and 'home_team_id' not in game_data:
            game_data['home_team_id'] = game_data['home_team']
        if 'away_team' in game_data and 'away_team_id' not in game_data:
            game_data['away_team_id'] = game_data['away_team']
        
        # Validate required fields
        required = ['home_team_id', 'away_team_id', 'game_date']
        for field in required:
            if field not in game_data or game_data[field] is None or game_data[field] == '':
                return {'error': f'Missing required field: {field}'}
        
        # Ensure home_team_id and away_team_id are integers
        try:
            game_data['home_team_id'] = int(game_data['home_team_id'])
            game_data['away_team_id'] = int(game_data['away_team_id'])
        except (ValueError, TypeError):
            return {'error': 'home_team_id and away_team_id must be integers'}
        
        # Generate game_id if not provided
        if 'game_id' not in game_data or not game_data['game_id']:
            game_data['game_id'] = f"{sport}_manual_{int(datetime.now().timestamp())}"
        
        # Set defaults
        game_data['sport'] = sport
        game_data['source'] = 'manual'
        
        # Add abbreviations if not provided
        if 'home_abbr' not in game_data or not game_data['home_abbr']:
            # Try to get from teams
            team = self.get_team_by_id(sport, game_data['home_team_id'], db)
            if team:
                game_data['home_abbr'] = team['abbreviation']
            else:
                game_data['home_abbr'] = f"T{game_data['home_team_id']}"
        
        if 'away_abbr' not in game_data or not game_data['away_abbr']:
            team = self.get_team_by_id(sport, game_data['away_team_id'], db)
            if team:
                game_data['away_abbr'] = team['abbreviation']
            else:
                game_data['away_abbr'] = f"T{game_data['away_team_id']}"
        
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
            # Normalize field names for bulk data too
            if 'home_team' in game_data and 'home_team_id' not in game_data:
                game_data['home_team_id'] = game_data['home_team']
            if 'away_team' in game_data and 'away_team_id' not in game_data:
                game_data['away_team_id'] = game_data['away_team']
            
            # Ensure integers
            try:
                if 'home_team_id' in game_data:
                    game_data['home_team_id'] = int(game_data['home_team_id'])
                if 'away_team_id' in game_data:
                    game_data['away_team_id'] = int(game_data['away_team_id'])
            except (ValueError, TypeError):
                errors.append({'index': i, 'error': 'home_team_id and away_team_id must be integers'})
                continue
            
            # Convert over_under to total if present
            if 'over_under' in game_data and 'total' not in game_data:
                game_data['total'] = game_data['over_under']
            
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