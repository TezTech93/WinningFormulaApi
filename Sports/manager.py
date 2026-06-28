# sports/manager.py
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta

from sports.nfl.api import NFLSport
from sports.nba.api import NBASport
from sports.mlb.api import MLBSport
from sports.nhl.api import NHLSport
from sports.ncaaf.api import NCAAFSport
from sports.ncaab.api import NCAABSport
from core.config import settings

logger = logging.getLogger(__name__)

# Sport instances cache
_sport_instances = {}

def get_sport_instance(sport: str):
    """Get or create a sport instance"""
    sport = sport.lower()
    
    if sport in _sport_instances:
        return _sport_instances[sport]
    
    sport_map = {
        'nfl': (NFLSport, settings.NFL_API_URL),
        'nba': (NBASport, settings.NBA_API_URL),
        'mlb': (MLBSport, settings.MLB_API_URL),
        'nhl': (NHLSport, settings.NHL_API_URL),
        'ncaaf': (NCAAFSport, settings.NCAAF_API_URL),
        'ncaab': (NCAABSport, settings.NCAAB_API_URL),
    }
    
    if sport not in sport_map:
        raise ValueError(f"Unsupported sport: {sport}")
    
    sport_class, api_url = sport_map[sport]
    instance = sport_class(api_url)
    _sport_instances[sport] = instance
    
    return instance

class SportsManager:
    """Unified manager for all sports"""
    
    SUPPORTED_SPORTS = ['nfl', 'nba', 'mlb', 'nhl', 'ncaaf', 'ncaab']
    
    @classmethod
    async def get_gamelines(cls, sport: str, source: str = None, force_refresh: bool = False) -> Dict[str, Any]:
        """Get gamelines for a specific sport"""
        try:
            sport_instance = get_sport_instance(sport)
            
            # Check cache first (unless force refresh)
            if not force_refresh:
                cached = sport_instance.get_cached_gamelines(source)
                if cached:
                    # Check if cache is fresh
                    for game in cached:
                        updated = game.get('updated_at', '')
                        if updated:
                            try:
                                updated_dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                                if datetime.now() - updated_dt < timedelta(minutes=settings.CACHE_EXPIRY_MINUTES):
                                    return {
                                        'sport': sport,
                                        'source': source or 'cached',
                                        'games': cached,
                                        'cached': True,
                                        'count': len(cached)
                                    }
                            except ValueError:
                                continue
                    # Cache is stale, continue to fetch
            
            # Fetch fresh data
            games = await sport_instance.fetch_gamelines(source)
            if games:
                return {
                    'sport': sport,
                    'source': source or 'espn_bets',
                    'games': games,
                    'cached': False,
                    'count': len(games)
                }
            
            # If fetch fails, return cached data even if stale
            cached = sport_instance.get_cached_gamelines(source)
            if cached:
                return {
                    'sport': sport,
                    'source': source or 'cached',
                    'games': cached,
                    'cached': True,
                    'stale': True,
                    'count': len(cached)
                }
            
            return {
                'sport': sport,
                'source': source or 'none',
                'games': [],
                'cached': False,
                'count': 0,
                'error': 'No data available'
            }
            
        except Exception as e:
            logger.error(f"Error getting {sport} gamelines: {e}")
            return {
                'sport': sport,
                'source': source or 'none',
                'games': [],
                'cached': False,
                'count': 0,
                'error': str(e)
            }
    
    @classmethod
    async def get_team_stats(cls, sport: str, team: str, year: str) -> Dict[str, Any]:
        """Get team stats for a specific sport"""
        try:
            sport_instance = get_sport_instance(sport)
            stats = await sport_instance.get_team_stats(team, year)
            return {
                'sport': sport,
                'team': team,
                'year': year,
                'stats': stats,
                'count': len(stats) if isinstance(stats, list) else 0
            }
        except Exception as e:
            logger.error(f"Error getting {sport} stats: {e}")
            return {
                'sport': sport,
                'team': team,
                'year': year,
                'stats': [],
                'count': 0,
                'error': str(e)
            }
    
    @classmethod
    def get_supported_sports(cls) -> List[str]:
        return cls.SUPPORTED_SPORTS
    
    @classmethod
    def get_sport_info(cls, sport: str) -> Dict[str, Any]:
        """Get information about a specific sport"""
        if sport not in cls.SUPPORTED_SPORTS:
            return {'error': f'Sport {sport} not supported'}
        
        sport_map = {
            'nfl': {'name': 'NFL', 'type': 'professional', 'logo': '🏈'},
            'nba': {'name': 'NBA', 'type': 'professional', 'logo': '🏀'},
            'mlb': {'name': 'MLB', 'type': 'professional', 'logo': '⚾'},
            'nhl': {'name': 'NHL', 'type': 'professional', 'logo': '🏒'},
            'ncaaf': {'name': 'NCAAF', 'type': 'college', 'logo': '🎯'},
            'ncaab': {'name': 'NCAAB', 'type': 'college', 'logo': '🏀'},
        }
        return sport_map.get(sport, {'error': 'Sport not found'})