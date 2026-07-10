# sports/nba/scraper.py
import datetime as dt
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from sports.base_scraper import BaseSportScraper
import logging

logger = logging.getLogger(__name__)

class NBAScraper(BaseSportScraper):
    def __init__(self):
        super().__init__('nba')
        self.base_url = 'https://www.basketball-reference.com'
        
        # NBA team abbreviations
        self.team_abbr_map = {
            'Atlanta Hawks': 'ATL', 'Boston Celtics': 'BOS',
            'Brooklyn Nets': 'BKN', 'Charlotte Hornets': 'CHA',
            'Chicago Bulls': 'CHI', 'Cleveland Cavaliers': 'CLE',
            'Dallas Mavericks': 'DAL', 'Denver Nuggets': 'DEN',
            'Detroit Pistons': 'DET', 'Golden State Warriors': 'GSW',
            'Houston Rockets': 'HOU', 'Indiana Pacers': 'IND',
            'Los Angeles Clippers': 'LAC', 'Los Angeles Lakers': 'LAL',
            'Memphis Grizzlies': 'MEM', 'Miami Heat': 'MIA',
            'Milwaukee Bucks': 'MIL', 'Minnesota Timberwolves': 'MIN',
            'New Orleans Pelicans': 'NOP', 'New York Knicks': 'NYK',
            'Oklahoma City Thunder': 'OKC', 'Orlando Magic': 'ORL',
            'Philadelphia 76ers': 'PHI', 'Phoenix Suns': 'PHX',
            'Portland Trail Blazers': 'POR', 'Sacramento Kings': 'SAC',
            'San Antonio Spurs': 'SAS', 'Toronto Raptors': 'TOR',
            'Utah Jazz': 'UTA', 'Washington Wizards': 'WAS'
        }
    
    def get_team_abbr(self, team_name: str) -> str:
        if not team_name:
            return 'N/A'
        return self.team_abbr_map.get(team_name.strip(), team_name[:3].upper())
    
    def get_gamelines(self) -> List[Dict[str, Any]]:
        """Fetch NBA gamelines from basketball-reference"""
        games = []
        
        try:
            current_year = dt.datetime.now().year
            url = f"{self.base_url}/leagues/NBA_{current_year}.html"
            soup = self.get_soup(url)
            
            if not soup:
                return games
            
            # Find the schedule table
            schedule_table = soup.find('table', {'id': 'schedule'})
            if not schedule_table:
                logger.warning("No NBA schedule table found")
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
                    is_completed = score_cell and score_cell.text.strip() and score_cell.text.strip() != '-'
                    
                    # Get time
                    time_cell = cells[4] if len(cells) > 4 else None
                    start_time = time_cell.text.strip() if time_cell else ''
                    
                    games.append({
                        'sport': 'nba',
                        'source': 'basketball-reference',
                        'game_id': f"nba_{len(games)}_{game_date.strftime('%Y%m%d')}",
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
                    logger.error(f"Error parsing NBA game row: {e}")
                    continue
            
            logger.info(f"Found {len(games)} NBA games")
            return games
            
        except Exception as e:
            logger.error(f"Error fetching NBA gamelines: {e}")
            return games
    
    def get_team_stats(self, team: str, year: str) -> List[Dict[str, Any]]:
        """Fetch NBA team stats from basketball-reference"""
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
        """Get current NBA season phase"""
        now = dt.datetime.now()
        current_year = now.year
        
        phase = {
            'phase': 'offseason',
            'season': f"{current_year-1}-{current_year}",
            'week': 0,
            'details': ''
        }
        
        # NBA season phases
        month = now.month
        
        if month in [10, 11, 12, 1, 2, 3, 4]:
            if month == 4:
                phase['phase'] = 'playoffs'
                phase['details'] = 'NBA Playoffs'
            elif month == 10 and now.day < 15:
                phase['phase'] = 'preseason'
                phase['details'] = 'Preseason'
            else:
                phase['phase'] = 'regular'
                phase['details'] = f'NBA Regular Season {current_year-1}-{current_year}'
        elif month in [5, 6]:
            phase['phase'] = 'playoffs'
            if month == 6:
                phase['details'] = 'NBA Finals'
            else:
                phase['details'] = 'NBA Playoffs'
        else:
            phase['phase'] = 'offseason'
            if month in [6, 7]:
                phase['details'] = 'NBA Draft / Free Agency'
            elif month in [8, 9]:
                phase['details'] = 'NBA Summer League / Training Camp Prep'
        
        return phase