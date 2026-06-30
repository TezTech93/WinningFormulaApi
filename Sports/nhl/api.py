# Sports/nhl/api.py
from Sports.base_sport import BaseSport
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# NHL Team abbreviations
NHL_TEAMS = {
    'Anaheim Ducks': 'ANA',
    'Arizona Coyotes': 'ARI',
    'Boston Bruins': 'BOS',
    'Buffalo Sabres': 'BUF',
    'Calgary Flames': 'CGY',
    'Carolina Hurricanes': 'CAR',
    'Chicago Blackhawks': 'CHI',
    'Colorado Avalanche': 'COL',
    'Columbus Blue Jackets': 'CBJ',
    'Dallas Stars': 'DAL',
    'Detroit Red Wings': 'DET',
    'Edmonton Oilers': 'EDM',
    'Florida Panthers': 'FLA',
    'Los Angeles Kings': 'LAK',
    'Minnesota Wild': 'MIN',
    'Montreal Canadiens': 'MTL',
    'Nashville Predators': 'NSH',
    'New Jersey Devils': 'NJD',
    'New York Islanders': 'NYI',
    'New York Rangers': 'NYR',
    'Ottawa Senators': 'OTT',
    'Philadelphia Flyers': 'PHI',
    'Pittsburgh Penguins': 'PIT',
    'San Jose Sharks': 'SJS',
    'Seattle Kraken': 'SEA',
    'St. Louis Blues': 'STL',
    'Tampa Bay Lightning': 'TBL',
    'Toronto Maple Leafs': 'TOR',
    'Vancouver Canucks': 'VAN',
    'Vegas Golden Knights': 'VGK',
    'Washington Capitals': 'WAS',
    'Winnipeg Jets': 'WPG',
}

class NHLSport(BaseSport):
    def __init__(self, api_url: str, db_path: str = "sports_data.db"):
        super().__init__("nhl", api_url, db_path)
    
    def get_team_abbr(self, team_name: str) -> str:
        if not team_name:
            return 'N/A'
        return NHL_TEAMS.get(team_name.strip(), team_name[:3].upper())
    
    def parse_gamelines(self, data: Dict) -> List[Dict]:
        """Parse NHL gameline data from API"""
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
        """Parse individual NHL games"""
        games = []
        for game in games_data:
            home_team = game.get('home', game.get('home_team', '')).strip()
            away_team = game.get('away', game.get('away_team', '')).strip()
            
            # NHL uses puck line instead of spread
            home_puckline = game.get('home_spread', game.get('home_puck_line', 'N/A'))
            away_puckline = game.get('away_spread', game.get('away_puck_line', 'N/A'))
            
            games.append({
                'game_id': game.get('game_id', f"nhl_{len(games)}"),
                'source': source,
                'home_team': home_team,
                'away_team': away_team,
                'home_abbr': self.get_team_abbr(home_team),
                'away_abbr': self.get_team_abbr(away_team),
                'home_ml': game.get('home_ml'),
                'away_ml': game.get('away_ml'),
                'home_spread': home_puckline,
                'away_spread': away_puckline,
                'home_spread_odds': game.get('home_spread_odds', game.get('home_puck_line_odds', -110)),
                'away_spread_odds': game.get('away_spread_odds', game.get('away_puck_line_odds', -110)),
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
            response = await self.client.get(f"{self.api_url}/nhl/{team}/{year}")
            response.raise_for_status()
            data = response.json()
            return data.get('Data', [])
        except Exception as e:
            logger.error(f"Error fetching NHL {team} stats: {e}")
            return []