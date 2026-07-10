# sports/nfl/scraper.py
import re
import json
import datetime as dt
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from sports.base_scraper import BaseSportScraper
import logging

logger = logging.getLogger(__name__)

class NFLScraper(BaseSportScraper):
    def __init__(self):
        super().__init__('nfl')
        self.base_url = 'https://www.pro-football-reference.com'
        
        # NFL team abbreviations mapping
        self.team_abbr_map = {
            'Arizona Cardinals': 'ARI', 'Atlanta Falcons': 'ATL',
            'Baltimore Ravens': 'BAL', 'Buffalo Bills': 'BUF',
            'Carolina Panthers': 'CAR', 'Chicago Bears': 'CHI',
            'Cincinnati Bengals': 'CIN', 'Cleveland Browns': 'CLE',
            'Dallas Cowboys': 'DAL', 'Denver Broncos': 'DEN',
            'Detroit Lions': 'DET', 'Green Bay Packers': 'GB',
            'Houston Texans': 'HOU', 'Indianapolis Colts': 'IND',
            'Jacksonville Jaguars': 'JAX', 'Kansas City Chiefs': 'KC',
            'Las Vegas Raiders': 'LV', 'Los Angeles Chargers': 'LAC',
            'Los Angeles Rams': 'LAR', 'Miami Dolphins': 'MIA',
            'Minnesota Vikings': 'MIN', 'New England Patriots': 'NE',
            'New Orleans Saints': 'NO', 'New York Giants': 'NYG',
            'New York Jets': 'NYJ', 'Philadelphia Eagles': 'PHI',
            'Pittsburgh Steelers': 'PIT', 'San Francisco 49ers': 'SF',
            'Seattle Seahawks': 'SEA', 'Tampa Bay Buccaneers': 'TB',
            'Tennessee Titans': 'TEN', 'Washington Commanders': 'WAS'
        }
    
    def get_team_abbr(self, team_name: str) -> str:
        if not team_name:
            return 'N/A'
        return self.team_abbr_map.get(team_name.strip(), team_name[:3].upper())
    
    def get_gamelines(self) -> List[Dict[str, Any]]:
        """Fetch NFL gamelines from pro-football-reference"""
        games = []
        
        try:
            # Get current week's games
            url = f"{self.base_url}/y/{dt.datetime.now().year}/week/"
            soup = self.get_soup(url)
            
            if not soup:
                return games
            
            # Find the schedule table
            schedule_table = soup.find('table', {'id': 'schedule'})
            if not schedule_table:
                logger.warning("No schedule table found")
                return games
            
            rows = schedule_table.find_all('tr')
            for row in rows:
                cells = row.find_all(['th', 'td'])
                if len(cells) < 4:
                    continue
                
                try:
                    # Extract game data
                    date_cell = cells[0]
                    away_cell = cells[1]
                    home_cell = cells[3]
                    
                    # Skip header rows or empty cells
                    if not date_cell.text.strip() or not away_cell.text.strip():
                        continue
                    
                    # Parse date
                    date_str = date_cell.text.strip()
                    try:
                        game_date = dt.datetime.strptime(date_str, '%Y-%m-%d')
                    except:
                        game_date = dt.datetime.now()
                    
                    away_team = away_cell.text.strip()
                    home_team = home_cell.text.strip()
                    
                    # Check if game has a score (completed)
                    score_cell = cells[2] if len(cells) > 2 else None
                    is_completed = score_cell and score_cell.text.strip() and score_cell.text.strip() != '-'
                    
                    # Get time if available
                    time_cell = cells[4] if len(cells) > 4 else None
                    start_time = time_cell.text.strip() if time_cell else ''
                    
                    games.append({
                        'sport': 'nfl',
                        'source': 'pro-football-reference',
                        'game_id': f"nfl_{len(games)}_{game_date.strftime('%Y%m%d')}",
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
                    logger.error(f"Error parsing NFL game row: {e}")
                    continue
            
            logger.info(f"Found {len(games)} NFL games")
            return games
            
        except Exception as e:
            logger.error(f"Error fetching NFL gamelines: {e}")
            return games
    
    def get_team_stats(self, team: str, year: str) -> List[Dict[str, Any]]:
        """Fetch NFL team stats from pro-football-reference"""
        all_stats = []
        url = f"{self.base_url}/teams/{team.lower()}/{year}/gamelog/"
        soup = self.get_soup(url)
        
        if not soup:
            return all_stats
        
        # Find all relevant rows
        rows = soup.find_all('tr', id=lambda x: x and x.startswith('table_pfr_team-year_game-logs_team-year-regular-season-game-log.'))
        
        for row in rows:
            game_data = {}
            cells = row.find_all(['th', 'td'], attrs={"data-stat": True})
            
            for cell in cells:
                stat_name = cell.get('data-stat')
                stat_value = cell.text.strip()
                
                if not stat_value or stat_name in ['ranker', 'team_game_num_season']:
                    continue
                
                game_data[stat_name] = stat_value
            
            if game_data:
                all_stats.append(game_data)
        
        logger.info(f"Found {len(all_stats)} games for {team} in {year}")
        return all_stats
    
    def get_season_phase(self) -> Dict[str, Any]:
        """Get current NFL season phase"""
        now = dt.datetime.now()
        current_year = now.year
        
        # NFL season phases by date
        # Typically: Preseason (Aug), Regular (Sep-Jan), Playoffs (Jan-Feb), Offseason (Feb-Jul)
        
        phase = {
            'phase': 'offseason',
            'season': current_year,
            'week': 0,
            'details': ''
        }
        
        try:
            url = f"{self.base_url}/y/{current_year}/"
            soup = self.get_soup(url)
            
            if not soup:
                return phase
            
            # Look for schedule info
            schedule_table = soup.find('table', {'id': 'schedule'})
            if schedule_table:
                # Count games to determine if season has started
                rows = schedule_table.find_all('tr')
                game_rows = [r for r in rows if r.find('td')]
                
                if game_rows:
                    # Check if any games have scores
                    completed = 0
                    for row in game_rows[:10]:  # Check first 10 games
                        cells = row.find_all('td')
                        if len(cells) > 2:
                            score_cell = cells[2]
                            if score_cell and score_cell.text.strip() and score_cell.text.strip() != '-':
                                completed += 1
                    
                    if completed > 0:
                        phase['phase'] = 'regular'
                    else:
                        phase['phase'] = 'preseason'
                    phase['week'] = len(game_rows)
                    phase['details'] = f"Week {len(game_rows)} of 17"
            
            # Determine phase by month
            month = now.month
            if month in [8, 9]:
                if phase['phase'] == 'regular':
                    phase['phase'] = 'regular'
                else:
                    phase['phase'] = 'preseason'
            elif month in [10, 11, 12, 1]:
                if month == 1 and now.day > 15:
                    phase['phase'] = 'playoffs'
                else:
                    phase['phase'] = 'regular'
            elif month in [2, 3, 4, 5, 6, 7]:
                phase['phase'] = 'offseason'
                if month in [2, 3]:
                    phase['details'] = 'Super Bowl / Free Agency'
                elif month in [4, 5]:
                    phase['details'] = 'NFL Draft / OTAs'
                elif month in [6, 7]:
                    phase['details'] = 'Training Camp'
            
            return phase
            
        except Exception as e:
            logger.error(f"Error getting NFL season phase: {e}")
            return phase