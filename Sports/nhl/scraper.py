# sports/nhl/scraper.py
import datetime as dt
import re
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from Sports.base_scraper import BaseSportScraper
import logging

logger = logging.getLogger(__name__)

class NHLScraper(BaseSportScraper):
    def __init__(self):
        super().__init__('nhl')
        self.base_url = 'https://www.hockey-reference.com'
        
        # NHL team abbreviations
        self.team_abbr_map = {
            'Anaheim Ducks': 'ANA', 'Arizona Coyotes': 'ARI',
            'Boston Bruins': 'BOS', 'Buffalo Sabres': 'BUF',
            'Calgary Flames': 'CGY', 'Carolina Hurricanes': 'CAR',
            'Chicago Blackhawks': 'CHI', 'Colorado Avalanche': 'COL',
            'Columbus Blue Jackets': 'CBJ', 'Dallas Stars': 'DAL',
            'Detroit Red Wings': 'DET', 'Edmonton Oilers': 'EDM',
            'Florida Panthers': 'FLA', 'Los Angeles Kings': 'LAK',
            'Minnesota Wild': 'MIN', 'Montreal Canadiens': 'MTL',
            'Nashville Predators': 'NSH', 'New Jersey Devils': 'NJD',
            'New York Islanders': 'NYI', 'New York Rangers': 'NYR',
            'Ottawa Senators': 'OTT', 'Philadelphia Flyers': 'PHI',
            'Pittsburgh Penguins': 'PIT', 'San Jose Sharks': 'SJS',
            'Seattle Kraken': 'SEA', 'St. Louis Blues': 'STL',
            'Tampa Bay Lightning': 'TBL', 'Toronto Maple Leafs': 'TOR',
            'Vancouver Canucks': 'VAN', 'Vegas Golden Knights': 'VGK',
            'Washington Capitals': 'WAS', 'Winnipeg Jets': 'WPG'
        }
    
    def get_team_abbr(self, team_name: str) -> str:
        if not team_name:
            return 'N/A'
        return self.team_abbr_map.get(team_name.strip(), team_name[:3].upper())
    
    def get_gamelines(self) -> List[Dict[str, Any]]:
        """Fetch NHL gamelines from hockey-reference"""
        games = []
        
        try:
            current_year = dt.datetime.now().year
            url = f"{self.base_url}/leagues/NHL_{current_year}.html"
            soup = self.get_soup(url)
            
            if not soup:
                return games
            
            # Find the schedule table
            schedule_table = soup.find('table', {'id': 'schedule'})
            if not schedule_table:
                logger.warning("No NHL schedule table found")
                return games
            
            rows = schedule_table.find_all('tr')
            for row in rows:
                cells = row.find_all(['th', 'td'])
                if len(cells) < 4:
                    continue
                
                try:
                    date_cell = cells[0]
                    away_cell = cells[1]
                    home_cell = cells[3]
                    
                    if not date_cell.text.strip():
                        continue
                    
                    # Parse date
                    date_str = date_cell.text.strip()
                    try:
                        game_date = dt.datetime.strptime(date_str, '%a, %b %d, %Y')
                    except:
                        try:
                            game_date = dt.datetime.strptime(date_str, '%Y-%m-%d')
                        except:
                            game_date = dt.datetime.now()
                    
                    away_team = away_cell.text.strip()
                    home_team = home_cell.text.strip()
                    
                    # Check if completed
                    score_cell = cells[2] if len(cells) > 2 else None
                    is_completed = score_cell and score_cell.text.strip() and 'vs' not in score_cell.text.strip()
                    
                    # Get time
                    time_cell = cells[4] if len(cells) > 4 else None
                    start_time = time_cell.text.strip() if time_cell else ''
                    
                    games.append({
                        'sport': 'nhl',
                        'source': 'hockey-reference',
                        'game_id': f"nhl_{len(games)}_{game_date.strftime('%Y%m%d')}",
                        'home': home_team,
                        'away': away_team,
                        'home_abbr': self.get_team_abbr(home_team),
                        'away_abbr': self.get_team_abbr(away_team),
                        'game_day': game_date.strftime('%Y-%m-%d'),
                        'start_time': start_time,
                        'is_completed': is_completed,
                        'home_ml': None,
                        'away_ml': None,
                        'home_spread': None,
                        'away_spread': None,
                        'home_spread_odds': None,
                        'away_spread_odds': None,
                        'over_under': None,
                        'over_odds': None,
                        'under_odds': None,
                    })
                except Exception as e:
                    logger.error(f"Error parsing NHL game row: {e}")
                    continue
            
            logger.info(f"Found {len(games)} NHL games")
            return games
            
        except Exception as e:
            logger.error(f"Error fetching NHL gamelines: {e}")
            return games
    
    def get_team_stats(self, team: str, year: str) -> List[Dict[str, Any]]:
        """Fetch NHL team stats from hockey-reference"""
        all_stats = []
        url = f"{self.base_url}/teams/{team.upper()}/{year}.html"
        soup = self.get_soup(url)
        
        if not soup:
            return all_stats
        
        # Find the stats table
        stats_table = soup.find('table', {'id': 'team_stats'})
        if not stats_table:
            return all_stats
        
        rows = stats_table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if not cells:
                continue
            
            game_data = {}
            for cell in cells:
                stat_name = cell.get('data-stat')
                if stat_name:
                    game_data[stat_name] = cell.text.strip()
            
            if game_data:
                all_stats.append(game_data)
        
        return all_stats
    
    def get_season_phase(self) -> Dict[str, Any]:
        """Get current NHL season phase"""
        now = dt.datetime.now()
        current_year = now.year
        
        phase = {
            'phase': 'offseason',
            'season': f"{current_year-1}-{current_year}",
            'week': 0,
            'details': ''
        }
        
        month = now.month
        
        if month in [10, 11, 12, 1, 2, 3, 4]:
            if month == 10 and now.day < 15:
                phase['phase'] = 'preseason'
                phase['details'] = 'Preseason'
            elif month == 4:
                phase['phase'] = 'playoffs'
                phase['details'] = 'Stanley Cup Playoffs'
            else:
                phase['phase'] = 'regular'
                phase['details'] = f'NHL Regular Season {current_year-1}-{current_year}'
        elif month in [5, 6]:
            phase['phase'] = 'playoffs'
            if month == 6:
                phase['details'] = 'Stanley Cup Finals'
            else:
                phase['details'] = 'Stanley Cup Playoffs'
        else:
            phase['phase'] = 'offseason'
            if month in [6, 7]:
                phase['details'] = 'NHL Draft / Free Agency'
            elif month in [8, 9]:
                phase['details'] = 'Training Camp Prep'
        
        return phase