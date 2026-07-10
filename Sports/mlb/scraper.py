# sports/mlb/scraper.py
import datetime as dt
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from sports.base_scraper import BaseSportScraper
import logging

logger = logging.getLogger(__name__)

class MLBSraper(BaseSportScraper):
    def __init__(self):
        super().__init__('mlb')
        self.base_url = 'https://www.baseball-reference.com'
        
        # MLB team abbreviations
        self.team_abbr_map = {
            'Arizona Diamondbacks': 'ARI', 'Atlanta Braves': 'ATL',
            'Baltimore Orioles': 'BAL', 'Boston Red Sox': 'BOS',
            'Chicago Cubs': 'CHC', 'Chicago White Sox': 'CWS',
            'Cincinnati Reds': 'CIN', 'Cleveland Guardians': 'CLE',
            'Colorado Rockies': 'COL', 'Detroit Tigers': 'DET',
            'Houston Astros': 'HOU', 'Kansas City Royals': 'KC',
            'Los Angeles Angels': 'LAA', 'Los Angeles Dodgers': 'LAD',
            'Miami Marlins': 'MIA', 'Milwaukee Brewers': 'MIL',
            'Minnesota Twins': 'MIN', 'New York Mets': 'NYM',
            'New York Yankees': 'NYY', 'Oakland Athletics': 'OAK',
            'Philadelphia Phillies': 'PHI', 'Pittsburgh Pirates': 'PIT',
            'San Diego Padres': 'SD', 'San Francisco Giants': 'SF',
            'Seattle Mariners': 'SEA', 'St. Louis Cardinals': 'STL',
            'Tampa Bay Rays': 'TB', 'Texas Rangers': 'TEX',
            'Toronto Blue Jays': 'TOR', 'Washington Nationals': 'WAS'
        }
    
    def get_team_abbr(self, team_name: str) -> str:
        if not team_name:
            return 'N/A'
        return self.team_abbr_map.get(team_name.strip(), team_name[:3].upper())
    
    def get_gamelines(self) -> List[Dict[str, Any]]:
        """Fetch MLB gamelines from baseball-reference"""
        games = []
        
        try:
            current_year = dt.datetime.now().year
            url = f"{self.base_url}/leagues/majors/{current_year}-schedule.shtml"
            soup = self.get_soup(url)
            
            if not soup:
                return games
            
            # Find schedule table
            schedule_table = soup.find('table', {'id': 'schedule'})
            if not schedule_table:
                # Try alternative table ID
                schedule_table = soup.find('table', {'class': 'schedule'})
            
            if not schedule_table:
                logger.warning("No MLB schedule table found")
                return games
            
            rows = schedule_table.find_all('tr')
            for row in rows:
                cells = row.find_all(['th', 'td'])
                if len(cells) < 3:
                    continue
                
                try:
                    date_cell = cells[0]
                    away_cell = cells[1]
                    home_cell = cells[2]
                    
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
                    
                    # Check if completed (look for score)
                    score_cell = cells[3] if len(cells) > 3 else None
                    is_completed = score_cell and score_cell.text.strip() and '(' not in score_cell.text.strip()
                    
                    games.append({
                        'sport': 'mlb',
                        'source': 'baseball-reference',
                        'game_id': f"mlb_{len(games)}_{game_date.strftime('%Y%m%d')}",
                        'home': home_team,
                        'away': away_team,
                        'home_abbr': self.get_team_abbr(home_team),
                        'away_abbr': self.get_team_abbr(away_team),
                        'game_day': game_date.strftime('%Y-%m-%d'),
                        'start_time': '',
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
                    logger.error(f"Error parsing MLB game row: {e}")
                    continue
            
            logger.info(f"Found {len(games)} MLB games")
            return games
            
        except Exception as e:
            logger.error(f"Error fetching MLB gamelines: {e}")
            return games
    
    def get_team_stats(self, team: str, year: str) -> List[Dict[str, Any]]:
        """Fetch MLB team stats from baseball-reference"""
        all_stats = []
        url = f"{self.base_url}/teams/{team.upper()}/{year}.shtml"
        soup = self.get_soup(url)
        
        if not soup:
            return all_stats
        
        # Find team batting stats
        batting_table = soup.find('table', {'id': 'team_batting'})
        if batting_table:
            rows = batting_table.find_all('tr')
            for row in rows[1:]:  # Skip header
                cells = row.find_all('td')
                if cells:
                    game_data = {}
                    for cell in cells:
                        stat_name = cell.get('data-stat')
                        if stat_name:
                            game_data[stat_name] = cell.text.strip()
                    if game_data:
                        all_stats.append(game_data)
        
        return all_stats
    
    def get_season_phase(self) -> Dict[str, Any]:
        """Get current MLB season phase"""
        now = dt.datetime.now()
        current_year = now.year
        
        phase = {
            'phase': 'offseason',
            'season': current_year,
            'week': 0,
            'details': ''
        }
        
        month = now.month
        
        if month in [3, 4, 5, 6, 7, 8, 9]:
            if month == 3 and now.day < 25:
                phase['phase'] = 'preseason'
                phase['details'] = 'Spring Training'
            elif month == 9:
                phase['phase'] = 'regular'
                phase['details'] = 'End of Regular Season'
            else:
                phase['phase'] = 'regular'
                phase['details'] = f'MLB Regular Season {current_year}'
        elif month == 10:
            phase['phase'] = 'playoffs'
            if now.day < 15:
                phase['details'] = 'MLB Postseason - Wild Card/Division Series'
            else:
                phase['details'] = 'MLB Postseason - League Championship Series'
        elif month == 11:
            phase['phase'] = 'playoffs'
            phase['details'] = 'World Series'
        else:
            phase['phase'] = 'offseason'
            if month in [11, 12]:
                phase['details'] = 'MLB Free Agency / Winter Meetings'
            elif month in [1, 2]:
                phase['details'] = 'MLB Hot Stove / Spring Training Prep'
        
        return phase