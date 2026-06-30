# Sports/mlb/api.py
from Sports.base_sport import BaseSport
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# MLB Team abbreviations
MLB_TEAMS = {
    'Arizona Diamondbacks': 'ARI',
    'Atlanta Braves': 'ATL',
    'Baltimore Orioles': 'BAL',
    'Boston Red Sox': 'BOS',
    'Chicago Cubs': 'CHC',
    'Chicago White Sox': 'CWS',
    'Cincinnati Reds': 'CIN',
    'Cleveland Guardians': 'CLE',
    'Colorado Rockies': 'COL',
    'Detroit Tigers': 'DET',
    'Houston Astros': 'HOU',
    'Kansas City Royals': 'KC',
    'Los Angeles Angels': 'LAA',
    'Los Angeles Dodgers': 'LAD',
    'Miami Marlins': 'MIA',
    'Milwaukee Brewers': 'MIL',
    'Minnesota Twins': 'MIN',
    'New York Mets': 'NYM',
    'New York Yankees': 'NYY',
    'Oakland Athletics': 'OAK',
    'Philadelphia Phillies': 'PHI',
    'Pittsburgh Pirates': 'PIT',
    'San Diego Padres': 'SD',
    'San Francisco Giants': 'SF',
    'Seattle Mariners': 'SEA',
    'St. Louis Cardinals': 'STL',
    'Tampa Bay Rays': 'TB',
    'Texas Rangers': 'TEX',
    'Toronto Blue Jays': 'TOR',
    'Washington Nationals': 'WAS',
}

class MLBSport(BaseSport):
    def __init__(self, api_url: str, db_path: str = "sports_data.db"):
        super().__init__("mlb", api_url, db_path)
    
    def get_team_abbr(self, team_name: str) -> str:
        if not team_name:
            return 'N/A'
        return MLB_TEAMS.get(team_name.strip(), team_name[:3].upper())
    
    def parse_gamelines(self, data: Dict) -> List[Dict]:
        """Parse MLB gameline data from API"""
        games = []
        
        if 'gamelines' in data and isinstance(data['gamelines'], list):
            for game in data['gamelines']:
                home_team = game.get('home_team', '').strip()
                away_team = game.get('away_team', '').strip()
                
                games.append({
                    'game_id': game.get('game_id', f"mlb_{len(games)}"),
                    'source': game.get('source', 'espn_bets'),
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
                    'total': game.get('over_under'),
                    'over_odds': game.get('over_odds', -110),
                    'under_odds': game.get('under_odds', -110),
                    'game_day': game.get('game_day', ''),
                    'start_time': game.get('start_time', ''),
                })
        
        return games
    
    async def get_team_stats(self, team: str, year: str) -> List[Dict]:
        """Get team stats from API"""
        try:
            response = await self.client.get(f"{self.api_url}/mlb/{team}/{year}")
            response.raise_for_status()
            data = response.json()
            return data.get('Data', [])
        except Exception as e:
            logger.error(f"Error fetching MLB {team} stats: {e}")
            return []