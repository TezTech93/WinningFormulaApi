# utils/seed_teams.py
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.database import SessionLocal
from models.team import Team

logger = logging.getLogger(__name__)

# NFL Teams data
NFL_TEAMS = [
    {'name': 'Arizona Cardinals', 'abbreviation': 'ARI', 'conference': 'NFC', 'division': 'West'},
    {'name': 'Atlanta Falcons', 'abbreviation': 'ATL', 'conference': 'NFC', 'division': 'South'},
    {'name': 'Baltimore Ravens', 'abbreviation': 'BAL', 'conference': 'AFC', 'division': 'North'},
    {'name': 'Buffalo Bills', 'abbreviation': 'BUF', 'conference': 'AFC', 'division': 'East'},
    {'name': 'Carolina Panthers', 'abbreviation': 'CAR', 'conference': 'NFC', 'division': 'South'},
    {'name': 'Chicago Bears', 'abbreviation': 'CHI', 'conference': 'NFC', 'division': 'North'},
    {'name': 'Cincinnati Bengals', 'abbreviation': 'CIN', 'conference': 'AFC', 'division': 'North'},
    {'name': 'Cleveland Browns', 'abbreviation': 'CLE', 'conference': 'AFC', 'division': 'North'},
    {'name': 'Dallas Cowboys', 'abbreviation': 'DAL', 'conference': 'NFC', 'division': 'East'},
    {'name': 'Denver Broncos', 'abbreviation': 'DEN', 'conference': 'AFC', 'division': 'West'},
    {'name': 'Detroit Lions', 'abbreviation': 'DET', 'conference': 'NFC', 'division': 'North'},
    {'name': 'Green Bay Packers', 'abbreviation': 'GB', 'conference': 'NFC', 'division': 'North'},
    {'name': 'Houston Texans', 'abbreviation': 'HOU', 'conference': 'AFC', 'division': 'South'},
    {'name': 'Indianapolis Colts', 'abbreviation': 'IND', 'conference': 'AFC', 'division': 'South'},
    {'name': 'Jacksonville Jaguars', 'abbreviation': 'JAX', 'conference': 'AFC', 'division': 'South'},
    {'name': 'Kansas City Chiefs', 'abbreviation': 'KC', 'conference': 'AFC', 'division': 'West'},
    {'name': 'Las Vegas Raiders', 'abbreviation': 'LV', 'conference': 'AFC', 'division': 'West'},
    {'name': 'Los Angeles Chargers', 'abbreviation': 'LAC', 'conference': 'AFC', 'division': 'West'},
    {'name': 'Los Angeles Rams', 'abbreviation': 'LAR', 'conference': 'NFC', 'division': 'West'},
    {'name': 'Miami Dolphins', 'abbreviation': 'MIA', 'conference': 'AFC', 'division': 'East'},
    {'name': 'Minnesota Vikings', 'abbreviation': 'MIN', 'conference': 'NFC', 'division': 'North'},
    {'name': 'New England Patriots', 'abbreviation': 'NE', 'conference': 'AFC', 'division': 'East'},
    {'name': 'New Orleans Saints', 'abbreviation': 'NO', 'conference': 'NFC', 'division': 'South'},
    {'name': 'New York Giants', 'abbreviation': 'NYG', 'conference': 'NFC', 'division': 'East'},
    {'name': 'New York Jets', 'abbreviation': 'NYJ', 'conference': 'AFC', 'division': 'East'},
    {'name': 'Philadelphia Eagles', 'abbreviation': 'PHI', 'conference': 'NFC', 'division': 'East'},
    {'name': 'Pittsburgh Steelers', 'abbreviation': 'PIT', 'conference': 'AFC', 'division': 'North'},
    {'name': 'San Francisco 49ers', 'abbreviation': 'SF', 'conference': 'NFC', 'division': 'West'},
    {'name': 'Seattle Seahawks', 'abbreviation': 'SEA', 'conference': 'NFC', 'division': 'West'},
    {'name': 'Tampa Bay Buccaneers', 'abbreviation': 'TB', 'conference': 'NFC', 'division': 'South'},
    {'name': 'Tennessee Titans', 'abbreviation': 'TEN', 'conference': 'AFC', 'division': 'South'},
    {'name': 'Washington Commanders', 'abbreviation': 'WAS', 'conference': 'NFC', 'division': 'East'},
]

# NBA Teams
NBA_TEAMS = [
    {'name': 'Atlanta Hawks', 'abbreviation': 'ATL', 'conference': 'Eastern', 'division': 'Southeast'},
    {'name': 'Boston Celtics', 'abbreviation': 'BOS', 'conference': 'Eastern', 'division': 'Atlantic'},
    {'name': 'Brooklyn Nets', 'abbreviation': 'BKN', 'conference': 'Eastern', 'division': 'Atlantic'},
    {'name': 'Charlotte Hornets', 'abbreviation': 'CHA', 'conference': 'Eastern', 'division': 'Southeast'},
    {'name': 'Chicago Bulls', 'abbreviation': 'CHI', 'conference': 'Eastern', 'division': 'Central'},
    {'name': 'Cleveland Cavaliers', 'abbreviation': 'CLE', 'conference': 'Eastern', 'division': 'Central'},
    {'name': 'Dallas Mavericks', 'abbreviation': 'DAL', 'conference': 'Western', 'division': 'Southwest'},
    {'name': 'Denver Nuggets', 'abbreviation': 'DEN', 'conference': 'Western', 'division': 'Northwest'},
    {'name': 'Detroit Pistons', 'abbreviation': 'DET', 'conference': 'Eastern', 'division': 'Central'},
    {'name': 'Golden State Warriors', 'abbreviation': 'GSW', 'conference': 'Western', 'division': 'Pacific'},
    {'name': 'Houston Rockets', 'abbreviation': 'HOU', 'conference': 'Western', 'division': 'Southwest'},
    {'name': 'Indiana Pacers', 'abbreviation': 'IND', 'conference': 'Eastern', 'division': 'Central'},
    {'name': 'Los Angeles Clippers', 'abbreviation': 'LAC', 'conference': 'Western', 'division': 'Pacific'},
    {'name': 'Los Angeles Lakers', 'abbreviation': 'LAL', 'conference': 'Western', 'division': 'Pacific'},
    {'name': 'Memphis Grizzlies', 'abbreviation': 'MEM', 'conference': 'Western', 'division': 'Southwest'},
    {'name': 'Miami Heat', 'abbreviation': 'MIA', 'conference': 'Eastern', 'division': 'Southeast'},
    {'name': 'Milwaukee Bucks', 'abbreviation': 'MIL', 'conference': 'Eastern', 'division': 'Central'},
    {'name': 'Minnesota Timberwolves', 'abbreviation': 'MIN', 'conference': 'Western', 'division': 'Northwest'},
    {'name': 'New Orleans Pelicans', 'abbreviation': 'NOP', 'conference': 'Western', 'division': 'Southwest'},
    {'name': 'New York Knicks', 'abbreviation': 'NYK', 'conference': 'Eastern', 'division': 'Atlantic'},
    {'name': 'Oklahoma City Thunder', 'abbreviation': 'OKC', 'conference': 'Western', 'division': 'Northwest'},
    {'name': 'Orlando Magic', 'abbreviation': 'ORL', 'conference': 'Eastern', 'division': 'Southeast'},
    {'name': 'Philadelphia 76ers', 'abbreviation': 'PHI', 'conference': 'Eastern', 'division': 'Atlantic'},
    {'name': 'Phoenix Suns', 'abbreviation': 'PHX', 'conference': 'Western', 'division': 'Pacific'},
    {'name': 'Portland Trail Blazers', 'abbreviation': 'POR', 'conference': 'Western', 'division': 'Northwest'},
    {'name': 'Sacramento Kings', 'abbreviation': 'SAC', 'conference': 'Western', 'division': 'Pacific'},
    {'name': 'San Antonio Spurs', 'abbreviation': 'SAS', 'conference': 'Western', 'division': 'Southwest'},
    {'name': 'Toronto Raptors', 'abbreviation': 'TOR', 'conference': 'Eastern', 'division': 'Atlantic'},
    {'name': 'Utah Jazz', 'abbreviation': 'UTA', 'conference': 'Western', 'division': 'Northwest'},
    {'name': 'Washington Wizards', 'abbreviation': 'WAS', 'conference': 'Eastern', 'division': 'Southeast'},
]

# MLB Teams
MLB_TEAMS = [
    {'name': 'Arizona Diamondbacks', 'abbreviation': 'ARI', 'conference': 'NL', 'division': 'West'},
    {'name': 'Atlanta Braves', 'abbreviation': 'ATL', 'conference': 'NL', 'division': 'East'},
    {'name': 'Baltimore Orioles', 'abbreviation': 'BAL', 'conference': 'AL', 'division': 'East'},
    {'name': 'Boston Red Sox', 'abbreviation': 'BOS', 'conference': 'AL', 'division': 'East'},
    {'name': 'Chicago Cubs', 'abbreviation': 'CHC', 'conference': 'NL', 'division': 'Central'},
    {'name': 'Chicago White Sox', 'abbreviation': 'CWS', 'conference': 'AL', 'division': 'Central'},
    {'name': 'Cincinnati Reds', 'abbreviation': 'CIN', 'conference': 'NL', 'division': 'Central'},
    {'name': 'Cleveland Guardians', 'abbreviation': 'CLE', 'conference': 'AL', 'division': 'Central'},
    {'name': 'Colorado Rockies', 'abbreviation': 'COL', 'conference': 'NL', 'division': 'West'},
    {'name': 'Detroit Tigers', 'abbreviation': 'DET', 'conference': 'AL', 'division': 'Central'},
    {'name': 'Houston Astros', 'abbreviation': 'HOU', 'conference': 'AL', 'division': 'West'},
    {'name': 'Kansas City Royals', 'abbreviation': 'KC', 'conference': 'AL', 'division': 'Central'},
    {'name': 'Los Angeles Angels', 'abbreviation': 'LAA', 'conference': 'AL', 'division': 'West'},
    {'name': 'Los Angeles Dodgers', 'abbreviation': 'LAD', 'conference': 'NL', 'division': 'West'},
    {'name': 'Miami Marlins', 'abbreviation': 'MIA', 'conference': 'NL', 'division': 'East'},
    {'name': 'Milwaukee Brewers', 'abbreviation': 'MIL', 'conference': 'NL', 'division': 'Central'},
    {'name': 'Minnesota Twins', 'abbreviation': 'MIN', 'conference': 'AL', 'division': 'Central'},
    {'name': 'New York Mets', 'abbreviation': 'NYM', 'conference': 'NL', 'division': 'East'},
    {'name': 'New York Yankees', 'abbreviation': 'NYY', 'conference': 'AL', 'division': 'East'},
    {'name': 'Oakland Athletics', 'abbreviation': 'OAK', 'conference': 'AL', 'division': 'West'},
    {'name': 'Philadelphia Phillies', 'abbreviation': 'PHI', 'conference': 'NL', 'division': 'East'},
    {'name': 'Pittsburgh Pirates', 'abbreviation': 'PIT', 'conference': 'NL', 'division': 'Central'},
    {'name': 'San Diego Padres', 'abbreviation': 'SD', 'conference': 'NL', 'division': 'West'},
    {'name': 'San Francisco Giants', 'abbreviation': 'SF', 'conference': 'NL', 'division': 'West'},
    {'name': 'Seattle Mariners', 'abbreviation': 'SEA', 'conference': 'AL', 'division': 'West'},
    {'name': 'St. Louis Cardinals', 'abbreviation': 'STL', 'conference': 'NL', 'division': 'Central'},
    {'name': 'Tampa Bay Rays', 'abbreviation': 'TB', 'conference': 'AL', 'division': 'East'},
    {'name': 'Texas Rangers', 'abbreviation': 'TEX', 'conference': 'AL', 'division': 'West'},
    {'name': 'Toronto Blue Jays', 'abbreviation': 'TOR', 'conference': 'AL', 'division': 'East'},
    {'name': 'Washington Nationals', 'abbreviation': 'WAS', 'conference': 'NL', 'division': 'East'},
]

# NHL Teams
NHL_TEAMS = [
    {'name': 'Anaheim Ducks', 'abbreviation': 'ANA', 'conference': 'Western', 'division': 'Pacific'},
    {'name': 'Arizona Coyotes', 'abbreviation': 'ARI', 'conference': 'Western', 'division': 'Central'},
    {'name': 'Boston Bruins', 'abbreviation': 'BOS', 'conference': 'Eastern', 'division': 'Atlantic'},
    {'name': 'Buffalo Sabres', 'abbreviation': 'BUF', 'conference': 'Eastern', 'division': 'Atlantic'},
    {'name': 'Calgary Flames', 'abbreviation': 'CGY', 'conference': 'Western', 'division': 'Pacific'},
    {'name': 'Carolina Hurricanes', 'abbreviation': 'CAR', 'conference': 'Eastern', 'division': 'Metropolitan'},
    {'name': 'Chicago Blackhawks', 'abbreviation': 'CHI', 'conference': 'Western', 'division': 'Central'},
    {'name': 'Colorado Avalanche', 'abbreviation': 'COL', 'conference': 'Western', 'division': 'Central'},
    {'name': 'Columbus Blue Jackets', 'abbreviation': 'CBJ', 'conference': 'Eastern', 'division': 'Metropolitan'},
    {'name': 'Dallas Stars', 'abbreviation': 'DAL', 'conference': 'Western', 'division': 'Central'},
    {'name': 'Detroit Red Wings', 'abbreviation': 'DET', 'conference': 'Eastern', 'division': 'Atlantic'},
    {'name': 'Edmonton Oilers', 'abbreviation': 'EDM', 'conference': 'Western', 'division': 'Pacific'},
    {'name': 'Florida Panthers', 'abbreviation': 'FLA', 'conference': 'Eastern', 'division': 'Atlantic'},
    {'name': 'Los Angeles Kings', 'abbreviation': 'LAK', 'conference': 'Western', 'division': 'Pacific'},
    {'name': 'Minnesota Wild', 'abbreviation': 'MIN', 'conference': 'Western', 'division': 'Central'},
    {'name': 'Montreal Canadiens', 'abbreviation': 'MTL', 'conference': 'Eastern', 'division': 'Atlantic'},
    {'name': 'Nashville Predators', 'abbreviation': 'NSH', 'conference': 'Western', 'division': 'Central'},
    {'name': 'New Jersey Devils', 'abbreviation': 'NJD', 'conference': 'Eastern', 'division': 'Metropolitan'},
    {'name': 'New York Islanders', 'abbreviation': 'NYI', 'conference': 'Eastern', 'division': 'Metropolitan'},
    {'name': 'New York Rangers', 'abbreviation': 'NYR', 'conference': 'Eastern', 'division': 'Metropolitan'},
    {'name': 'Ottawa Senators', 'abbreviation': 'OTT', 'conference': 'Eastern', 'division': 'Atlantic'},
    {'name': 'Philadelphia Flyers', 'abbreviation': 'PHI', 'conference': 'Eastern', 'division': 'Metropolitan'},
    {'name': 'Pittsburgh Penguins', 'abbreviation': 'PIT', 'conference': 'Eastern', 'division': 'Metropolitan'},
    {'name': 'San Jose Sharks', 'abbreviation': 'SJS', 'conference': 'Western', 'division': 'Pacific'},
    {'name': 'Seattle Kraken', 'abbreviation': 'SEA', 'conference': 'Western', 'division': 'Pacific'},
    {'name': 'St. Louis Blues', 'abbreviation': 'STL', 'conference': 'Western', 'division': 'Central'},
    {'name': 'Tampa Bay Lightning', 'abbreviation': 'TBL', 'conference': 'Eastern', 'division': 'Atlantic'},
    {'name': 'Toronto Maple Leafs', 'abbreviation': 'TOR', 'conference': 'Eastern', 'division': 'Atlantic'},
    {'name': 'Vancouver Canucks', 'abbreviation': 'VAN', 'conference': 'Western', 'division': 'Pacific'},
    {'name': 'Vegas Golden Knights', 'abbreviation': 'VGK', 'conference': 'Western', 'division': 'Pacific'},
    {'name': 'Washington Capitals', 'abbreviation': 'WAS', 'conference': 'Eastern', 'division': 'Metropolitan'},
    {'name': 'Winnipeg Jets', 'abbreviation': 'WPG', 'conference': 'Western', 'division': 'Central'},
]

# All teams grouped by sport
ALL_TEAMS = {
    'nfl': NFL_TEAMS,
    'nba': NBA_TEAMS,
    'mlb': MLB_TEAMS,
    'nhl': NHL_TEAMS,
}


def seed_teams(db: Session, sport: str = None):
    """
    Seed teams for a specific sport or all sports
    
    Args:
        db: SQLAlchemy session
        sport: Optional sport name ('nfl', 'nba', 'mlb', 'nhl')
    
    Returns:
        dict: Summary of seeded teams
    """
    results = {}
    
    sports_to_seed = [sport] if sport else ALL_TEAMS.keys()
    
    for sport_name in sports_to_seed:
        if sport_name not in ALL_TEAMS:
            logger.warning(f"Sport '{sport_name}' not found in team data")
            continue
        
        team_data = ALL_TEAMS[sport_name]
        added = 0
        skipped = 0
        
        for team_info in team_data:
            # Check if team already exists
            existing = db.query(Team).filter(
                Team.sport == sport_name,
                Team.abbreviation == team_info['abbreviation']
            ).first()
            
            if existing:
                skipped += 1
                continue
            
            # Create new team
            team = Team(
                sport=sport_name,
                name=team_info['name'],
                abbreviation=team_info['abbreviation'],
                conference=team_info.get('conference'),
                division=team_info.get('division'),
            )
            db.add(team)
            added += 1
        
        db.commit()
        results[sport_name] = {
            'added': added,
            'skipped': skipped,
            'total': len(team_data)
        }
        logger.info(f"Seeded {sport_name.upper()}: {added} added, {skipped} skipped")
    
    return results


def seed_nfl_teams(db: Session):
    """Seed only NFL teams"""
    return seed_teams(db, 'nfl')


def seed_all_teams(db: Session):
    """Seed all teams"""
    return seed_teams(db)


def get_team_id(db: Session, sport: str, abbreviation: str) -> int:
    """Get team ID by sport and abbreviation"""
    team = db.query(Team).filter(
        Team.sport == sport,
        Team.abbreviation == abbreviation
    ).first()
    return team.id if team else None


def get_team_mapping(db: Session, sport: str) -> dict:
    """Get mapping of abbreviation -> ID for a sport"""
    teams = db.query(Team).filter(Team.sport == sport).all()
    return {team.abbreviation: team.id for team in teams}


if __name__ == "__main__":
    # Run directly to seed all teams
    db = SessionLocal()
    try:
        print("Seeding teams...")
        results = seed_all_teams(db)
        print("\nSeeding Results:")
        for sport, data in results.items():
            print(f"  {sport.upper()}: {data['added']} added, {data['skipped']} skipped, {data['total']} total")
        print("\n✅ Teams seeded successfully!")
    except Exception as e:
        print(f"❌ Error seeding teams: {e}")
        db.rollback()
    finally:
        db.close()