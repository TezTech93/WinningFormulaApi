# sports/ncaab/scraper.py
import datetime as dt
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from Sports.base_scraper import BaseSportScraper
import logging

logger = logging.getLogger(__name__)

class NCAABScraper(BaseSportScraper):
    def __init__(self):
        super().__init__('ncaab')
        self.base_url = 'https://www.sports-reference.com/cbb'
        
        # NCAAB team abbreviations (partial - will be populated from data)
        self.team_abbr_map = {
            'Duke Blue Devils': 'DUKE', 'Kansas Jayhawks': 'KU',
            'North Carolina Tar Heels': 'UNC', 'Kentucky Wildcats': 'UK',
            'Michigan State Spartans': 'MSU', 'Gonzaga Bulldogs': 'GONZ',
            'Arizona Wildcats': 'ARIZ', 'UCLA Bruins': 'UCLA',
            'Indiana Hoosiers': 'IND', 'Ohio State Buckeyes': 'OSU',
            'Baylor Bears': 'BAY', 'Houston Cougars': 'HOU',
            'Alabama Crimson Tide': 'BAMA', 'Tennessee Volunteers': 'TENN',
            'Texas Longhorns': 'TEX', 'USC Trojans': 'USC',
            'Villanova Wildcats': 'VILL', 'UConn Huskies': 'CONN',
            'Florida Gators': 'UF', 'Louisville Cardinals': 'LOU',
            'Syracuse Orange': 'SYR', 'Purdue Boilermakers': 'PUR',
            'Wisconsin Badgers': 'WIS', 'Iowa Hawkeyes': 'IOWA',
            'Michigan Wolverines': 'MICH', 'Maryland Terrapins': 'MD',
            'Creighton Bluejays': 'CREI', 'Xavier Musketeers': 'XAV',
            'Marquette Golden Eagles': 'MARQ', 'St. John\'s Red Storm': 'SJU',
            'Georgetown Hoyas': 'GTWN', 'Butler Bulldogs': 'BUT',
            'Providence Friars': 'PROV', 'Seton Hall Pirates': 'SHU',
            'Memphis Tigers': 'MEM', 'Cincinnati Bearcats': 'CIN',
            'Florida Atlantic Owls': 'FAU', 'San Diego State Aztecs': 'SDSU',
            'Colorado State Rams': 'CSU', 'Saint Mary\'s Gaels': 'SMC',
            'Nevada Wolf Pack': 'NEV', 'New Mexico Lobos': 'NM',
            'VCU Rams': 'VCU', 'Dayton Flyers': 'DAY',
            'St. Bonaventure Bonnies': 'SBU', 'Davidson Wildcats': 'DAV',
            'Richmond Spiders': 'RICH', 'Loyola Chicago Ramblers': 'LUC',
            'Drake Bulldogs': 'DRKE', 'Bradley Braves': 'BRAD',
            'Northern Iowa Panthers': 'UNI', 'Belmont Bruins': 'BEL'
        }
    
    def get_team_abbr(self, team_name: str) -> str:
        if not team_name:
            return 'N/A'
        return self.team_abbr_map.get(team_name.strip(), team_name[:3].upper())
    
    def get_gamelines(self) -> List[Dict[str, Any]]:
        """Fetch NCAAB gamelines from sports-reference"""
        games = []
        
        try:
            current_year = dt.datetime.now().year
            url = f"{self.base_url}/years/{current_year}/schedule.html"
            soup = self.get_soup(url)
            
            if not soup:
                return games
            
            # Find schedule table
            schedule_table = soup.find('table', {'id': 'schedule'})
            if not schedule_table:
                logger.warning("No NCAAB schedule table found")
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
                        game_date = dt.datetime.strptime(date_str, '%Y-%m-%d')
                    except:
                        try:
                            game_date = dt.datetime.strptime(date_str, '%b %d, %Y')
                        except:
                            game_date = dt.datetime.now()
                    
                    away_team = away_cell.text.strip()
                    home_team = home_cell.text.strip()
                    
                    # Check if completed
                    score_cell = cells[3] if len(cells) > 3 else None
                    is_completed = score_cell and score_cell.text.strip() and 'vs' not in score_cell.text.strip()
                    
                    games.append({
                        'sport': 'ncaab',
                        'source': 'sports-reference',
                        'game_id': f"ncaab_{len(games)}_{game_date.strftime('%Y%m%d')}",
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
                    logger.error(f"Error parsing NCAAB game row: {e}")
                    continue
            
            logger.info(f"Found {len(games)} NCAAB games")
            return games
            
        except Exception as e:
            logger.error(f"Error fetching NCAAB gamelines: {e}")
            return games
    
    def get_team_stats(self, team: str, year: str) -> List[Dict[str, Any]]:
        """Fetch NCAAB team stats from sports-reference"""
        all_stats = []
        
        # Try to find team in the mapping
        team_lower = team.lower()
        for full_name, abbr in self.team_abbr_map.items():
            if team_lower in full_name.lower() or abbr.lower() == team_lower:
                team_abbr = abbr
                break
        else:
            team_abbr = team[:3].upper()
        
        url = f"{self.base_url}/schools/{team_abbr.lower()}/{year}/gamelog.html"
        soup = self.get_soup(url)
        
        if not soup:
            return all_stats
        
        # Find the stats table
        stats_table = soup.find('table', {'id': 'gamelog'})
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
        """Get current NCAAB season phase"""
        now = dt.datetime.now()
        current_year = now.year
        
        phase = {
            'phase': 'offseason',
            'season': f"{current_year-1}-{current_year}",
            'week': 0,
            'details': ''
        }
        
        month = now.month
        
        if month in [11, 12, 1, 2, 3, 4]:
            if month == 11 and now.day < 15:
                phase['phase'] = 'preseason'
                phase['details'] = 'Preseason / Exhibition Games'
            elif month == 3:
                phase['phase'] = 'playoffs'
                phase['details'] = 'Conference Tournaments'
            elif month == 4:
                phase['phase'] = 'playoffs'
                phase['details'] = 'NCAA Tournament - Final Four / Championship'
            else:
                phase['phase'] = 'regular'
                phase['details'] = f'NCAAB Regular Season {current_year-1}-{current_year}'
        else:
            phase['phase'] = 'offseason'
            if month in [5, 6]:
                phase['details'] = 'Recruiting / NBA Draft'
            elif month in [7, 8, 9, 10]:
                phase['details'] = 'Summer Training / Season Prep'
        
        return phase