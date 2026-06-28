# sports/ncaaf/api.py
from sports.base_sport import BaseSport
from typing import Dict, Any, List, Optional
import logging
from utils.ncaaf_teams import get_ncaaf_team_by_abbr

logger = logging.getLogger(__name__)

class NCAAFSport(BaseSport):
    def __init__(self, api_url: str, db_path: str = "sports_data.db"):
        super().__init__("ncaaf", api_url, db_path)
    
    def get_team_abbr(self, team_name: str) -> str:
        if not team_name:
            return 'N/A'
        # Try to find in NCAAF teams list
        team = get_ncaaf_team_by_abbr(team_name)
        if team:
            return team['abbr']
        # Try to find by name
        from utils.ncaaf_teams import NCAAF_TEAMS
        for t in NCAAF_TEAMS:
            if t['name'].lower() in team_name.lower() or team_name.lower() in t['name'].lower():
                return t['abbr']
        return team_name[:3].upper()
    
    def parse_gamelines(self, data: Dict) -> List[Dict]:
        """Parse NCAAF gameline data"""
        games = []
        
        if 'Gamelines' in data and isinstance(data['Gamelines'], dict):
            for source, games_data in data['Gamelines'].items():
                if games_data and isinstance(games_data, list):
                    games = self._parse_games(games_data, source)
                    break
        elif 'gamelines' in data and isinstance(data['gamelines'], list):
            games = self._parse_games(data['gamelines'], 'espn_bets')
        elif isinstance(data, list):
            games = self._parse_games(data, 'espn_bets')
        
        return games
    
    def _parse_games(self, games_data: List[Dict], source: str) -> List[Dict]:
        """Parse individual NCAAF games"""
        games = []
        for game in games_data:
            home_team = game.get('home', game.get('home_team', '')).strip()
            away_team = game.get('away', game.get('away_team', '')).strip()
            
            games.append({
                'game_id': game.get('game_id', f"ncaaf_{len(games)}"),
                'source': source,
                'home_team': home_team,
                'away_team': away_team,
                'home_abbr': self.get_team_abbr(home_team),
                'away_abbr': self.get_team_abbr(away_team),
                'home_ml': game.get('home_ml'),
                'away_ml': game.get('away_ml'),
                'home_spread': game.get('home_spread'),
                'away_spread': game.get('away_spread'),
                'home_spread_odds': game.get('home_spread_odds', -110),
                'away_spread_odds': game.get('away_spread_odds', -110),
                'total': game.get('total', game.get('over_under')),
                'over_odds': game.get('over_odds', -110),
                'under_odds': game.get('under_odds', -110),
                'game_day': game.get('game_day', game.get('date', '')),
                'start_time': game.get('start_time', ''),
            })
        return games
    
    async def get_team_stats(self, team: str, year: str) -> List[Dict]:
        """Get team stats from API"""
        try:
            # Try the team stats endpoint
            response = await self.client.get(f"{self.api_url}/{team}/{year}")
            response.raise_for_status()
            data = response.json()
            return data.get('Data', [])
        except Exception as e:
            logger.error(f"Error fetching NCAAF {team} stats: {e}")
            return []