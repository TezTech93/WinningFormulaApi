# sports/ncaaf/scraper.py
import datetime as dt
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from sports.base_scraper import BaseSportScraper
import logging

logger = logging.getLogger(__name__)

class NCAAFScraper(BaseSportScraper):
    def __init__(self):
        super().__init__('ncaaf')
        self.base_url = 'https://www.sports-reference.com/cfb'
        
        # NCAAF team abbreviations (partial - will be populated from data)
        self.team_abbr_map = {
            'Ohio State Buckeyes': 'OSU', 'Alabama Crimson Tide': 'BAMA',
            'Georgia Bulldogs': 'UGA', 'Michigan Wolverines': 'MICH',
            'Michigan State Spartans': 'MSU', 'Clemson Tigers': 'CLEM',
            'Notre Dame Fighting Irish': 'ND', 'USC Trojans': 'USC',
            'Florida Gators': 'UF', 'Texas Longhorns': 'TEX',
            'Oklahoma Sooners': 'OU', 'Oregon Ducks': 'ORE',
            'Penn State Nittany Lions': 'PSU', 'LSU Tigers': 'LSU',
            'Auburn Tigers': 'AUB', 'Tennessee Volunteers': 'TENN',
            'Florida State Seminoles': 'FSU', 'Miami Hurricanes': 'MIAMI',
            'Wisconsin Badgers': 'WIS', 'Iowa Hawkeyes': 'IOWA',
            'Washington Huskies': 'WASH', 'Oregon State Beavers': 'ORST',
            'Utah Utes': 'UTAH', 'UCLA Bruins': 'UCLA',
            'Stanford Cardinal': 'STAN', 'Arizona Wildcats': 'ARIZ',
            'Arizona State Sun Devils': 'ASU', 'Colorado Buffaloes': 'COLO',
            'Kansas State Wildcats': 'KSU', 'TCU Horned Frogs': 'TCU',
            'Baylor Bears': 'BAY', 'Texas Tech Red Raiders': 'TTU',
            'Oklahoma State Cowboys': 'OKST', 'West Virginia Mountaineers': 'WVU',
            'BYU Cougars': 'BYU', 'North Carolina Tar Heels': 'UNC',
            'Virginia Tech Hokies': 'VT', 'Pittsburgh Panthers': 'PITT',
            'Syracuse Orange': 'SYR', 'Wake Forest Demon Deacons': 'WAKE',
            'NC State Wolfpack': 'NCST', 'Louisville Cardinals': 'LOU',
            'Duke Blue Devils': 'DUKE', 'Boston College Eagles': 'BC',
            'California Golden Bears': 'CAL', 'Maryland Terrapins': 'MD',
            'Rutgers Scarlet Knights': 'RUTG', 'Indiana Hoosiers': 'IND',
            'Purdue Boilermakers': 'PUR', 'Northwestern Wildcats': 'NW',
            'Minnesota Golden Gophers': 'MINN', 'Nebraska Cornhuskers': 'NEB',
            'Illinois Fighting Illini': 'ILL', 'Kansas Jayhawks': 'KU',
            'Iowa State Cyclones': 'ISU', 'Cincinnati Bearcats': 'CIN',
            'Houston Cougars': 'HOU', 'UCF Knights': 'UCF',
            'Memphis Tigers': 'MEM', 'South Carolina Gamecocks': 'SCAR',
            'Missouri Tigers': 'MIZZ', 'Kentucky Wildcats': 'UK',
            'Ole Miss Rebels': 'MISS', 'Mississippi State Bulldogs': 'MSST',
            'Arkansas Razorbacks': 'ARK', 'Vanderbilt Commodores': 'VANDY',
            'Texas A&M Aggies': 'TAMU', 'Georgia Tech Yellow Jackets': 'GT',
            'SMU Mustangs': 'SMU', 'Rice Owls': 'RICE',
            'Tulane Green Wave': 'TULN', 'Navy Midshipmen': 'NAVY',
            'Army Black Knights': 'ARMY', 'Air Force Falcons': 'AFA',
            'Boise State Broncos': 'BSU', 'Fresno State Bulldogs': 'FRES',
            'San Diego State Aztecs': 'SDSU', 'Appalachian State Mountaineers': 'APP',
            'Coastal Carolina Chanticleers': 'CCU', 'James Madison Dukes': 'JMU',
            'Liberty Flames': 'LIB', 'Western Kentucky Hilltoppers': 'WKU'
        }
    
    def get_team_abbr(self, team_name: str) -> str:
        if not team_name:
            return 'N/A'
        return self.team_abbr_map.get(team_name.strip(), team_name[:3].upper())
    
    def get_gamelines(self) -> List[Dict[str, Any]]:
        """Fetch NCAAF gamelines from sports-reference"""
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
                logger.warning("No NCAAF schedule table found")
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
                        'sport': 'ncaaf',
                        'source': 'sports-reference',
                        'game_id': f"ncaaf_{len(games)}_{game_date.strftime('%Y%m%d')}",
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
                    logger.error(f"Error parsing NCAAF game row: {e}")
                    continue
            
            logger.info(f"Found {len(games)} NCAAF games")
            return games
            
        except Exception as e:
            logger.error(f"Error fetching NCAAF gamelines: {e}")
            return games
    
    def get_team_stats(self, team: str, year: str) -> List[Dict[str, Any]]:
        """Fetch NCAAF team stats from sports-reference"""
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
        """Get current NCAAF season phase"""
        now = dt.datetime.now()
        current_year = now.year
        
        phase = {
            'phase': 'offseason',
            'season': current_year,
            'week': 0,
            'details': ''
        }
        
        month = now.month
        
        if month in [8, 9, 10, 11, 12]:
            if month == 8 and now.day < 25:
                phase['phase'] = 'preseason'
                phase['details'] = 'Preseason / Training Camp'
            elif month == 12:
                phase['phase'] = 'playoffs'
                phase['details'] = 'Bowl Season / Playoffs'
            else:
                phase['phase'] = 'regular'
                phase['details'] = f'NCAAF Regular Season {current_year}'
        elif month == 1:
            phase['phase'] = 'playoffs'
            phase['details'] = 'College Football Playoff National Championship'
        else:
            phase['phase'] = 'offseason'
            if month in [2, 3, 4]:
                phase['details'] = 'National Signing Day / Spring Practice'
            elif month in [5, 6, 7]:
                phase['details'] = 'Summer Training / Season Prep'
        
        return phase