# services/sports_api.py
import httpx
import logging
from typing import Dict, Any, Optional
from core.config import settings

logger = logging.getLogger(__name__)

class SportsAPIService:
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
        self.api_urls = {
            'nfl': settings.NFL_API_URL,
            'nba': settings.NBA_API_URL,
            'mlb': settings.MLB_API_URL,
            'nhl': settings.NHL_API_URL,
            'ncaaf': settings.NCAAF_API_URL,
            'ncaab': settings.NCAAB_API_URL,
        }
    
    async def fetch_gamelines(self, sport: str, source: str = 'espn_bets') -> Optional[Dict[str, Any]]:
        """Fetch gamelines from sport-specific API"""
        try:
            url = self.api_urls.get(sport)
            if not url:
                logger.error(f"No API URL found for sport: {sport}")
                return None
            
            response = await self.client.get(f"{url}/gamelines")
            response.raise_for_status()
            
            data = response.json()
            
            # Parse and normalize data
            return self._parse_gamelines(data, sport, source)
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {sport} gamelines: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {sport} gamelines: {e}")
            return None
    
    def _parse_gamelines(self, data: Dict, sport: str, source: str) -> Dict[str, Any]:
        """Parse sport-specific gameline data into standard format"""
        games = []
        
        # Parse based on sport API structure
        if sport == 'nfl':
            games = self._parse_nfl(data, source)
        elif sport == 'nba':
            games = self._parse_nba(data, source)
        elif sport == 'mlb':
            games = self._parse_mlb(data, source)
        elif sport == 'nhl':
            games = self._parse_nhl(data, source)
        elif sport == 'ncaaf':
            games = self._parse_ncaaf(data, source)
        elif sport == 'ncaab':
            games = self._parse_ncaab(data, source)
        
        return {'sport': sport, 'source': source, 'games': games}
    
    def _parse_nfl(self, data: Dict, source: str) -> list:
        """Parse NFL gameline data"""
        games = []
        gamelines = data.get('Gamelines', {})
        games_data = gamelines.get(source, gamelines.get('espn_bets', []))
        
        for game in games_data:
            games.append({
                'game_id': game.get('game_id', f"nfl_{len(games)}"),
                'home_team': game.get('home', ''),
                'away_team': game.get('away', ''),
                'home_abbr': self._get_team_abbr(game.get('home', ''), 'nfl'),
                'away_abbr': self._get_team_abbr(game.get('away', ''), 'nfl'),
                'home_ml': game.get('home_ml'),
                'away_ml': game.get('away_ml'),
                'home_spread': game.get('home_spread'),
                'away_spread': game.get('away_spread'),
                'home_spread_odds': game.get('home_spread_odds', -110),
                'away_spread_odds': game.get('away_spread_odds', -110),
                'total': game.get('total') or game.get('over_under'),
                'over_odds': game.get('over_odds', -110),
                'under_odds': game.get('under_odds', -110),
                'game_date': game.get('game_day'),
                'start_time': game.get('start_time'),
            })
        return games
    
    def _parse_nba(self, data: Dict, source: str) -> list:
        """Parse NBA gameline data"""
        games = []
        gamelines = data.get('Gamelines', {})
        games_data = gamelines.get(source, gamelines.get('espn_bets', []))
        
        for game in games_data:
            games.append({
                'game_id': game.get('game_id', f"nba_{len(games)}"),
                'home_team': game.get('home') or game.get('home_team', ''),
                'away_team': game.get('away') or game.get('away_team', ''),
                'home_abbr': self._get_team_abbr(game.get('home') or game.get('home_team', ''), 'nba'),
                'away_abbr': self._get_team_abbr(game.get('away') or game.get('away_team', ''), 'nba'),
                'home_ml': game.get('home_ml'),
                'away_ml': game.get('away_ml'),
                'home_spread': game.get('home_spread'),
                'away_spread': game.get('away_spread'),
                'home_spread_odds': game.get('home_spread_odds', -110),
                'away_spread_odds': game.get('away_spread_odds', -110),
                'total': game.get('total') or game.get('over_under'),
                'over_odds': game.get('over_odds', -110),
                'under_odds': game.get('under_odds', -110),
                'game_date': game.get('game_day'),
                'start_time': game.get('start_time'),
            })
        return games
    
    def _parse_mlb(self, data: Dict, source: str) -> list:
        """Parse MLB gameline data"""
        games = []
        gamelines = data.get('gamelines', [])
        
        for game in gamelines:
            if game.get('source') != source:
                continue
            games.append({
                'game_id': game.get('game_id', f"mlb_{len(games)}"),
                'home_team': game.get('home_team', ''),
                'away_team': game.get('away_team', ''),
                'home_abbr': self._get_team_abbr(game.get('home_team', ''), 'mlb'),
                'away_abbr': self._get_team_abbr(game.get('away_team', ''), 'mlb'),
                'home_ml': game.get('home_ml'),
                'away_ml': game.get('away_ml'),
                'home_spread': game.get('home_spread'),
                'away_spread': game.get('away_spread'),
                'home_spread_odds': game.get('home_spread_odds', -110),
                'away_spread_odds': game.get('away_spread_odds', -110),
                'total': game.get('over_under'),
                'over_odds': game.get('over_odds', -110),
                'under_odds': game.get('under_odds', -110),
                'game_date': game.get('game_day'),
                'start_time': game.get('start_time'),
            })
        return games
    
    def _get_team_abbr(self, team_name: str, sport: str) -> str:
        """Get team abbreviation from full name"""
        from utils.helpers import get_team_abbreviation
        return get_team_abbreviation(team_name, sport)