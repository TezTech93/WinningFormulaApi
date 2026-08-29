# utils/team_resolver.py
import unicodedata
from sqlalchemy.orm import Session
from models.team import Team

def normalize_string(s: str) -> str:
    """Remove accents, convert to lowercase, strip extra spaces."""
    s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8')
    return s.lower().strip()

def get_team_id(sport: str, search_name: str, db: Session, team_list=None) -> int:
    """
    Resolve a team name to its database ID using multiple strategies.
    team_list is a list of dicts with keys: city, teamName, abv.
    """
    if not search_name:
        return None

    norm_search = normalize_string(search_name)
    teams = db.query(Team).filter(Team.sport == sport).all()

    # 1. Exact case-insensitive match
    for t in teams:
        if t.name.lower() == search_name.lower():
            return t.id

    # 2. Normalized exact match
    for t in teams:
        if normalize_string(t.name) == norm_search:
            return t.id

    # 3. Partial match (substring)
    for t in teams:
        t_norm = normalize_string(t.name)
        if norm_search in t_norm or t_norm in norm_search:
            return t.id

    # 4. Match by city + teamName using the team_list
    if team_list:
        # Try to find a team_info where city+teamName forms the search name
        for team_info in team_list:
            city = team_info.get('city', '').strip()
            team_name = team_info.get('teamName', '').strip()
            full_name = f"{city} {team_name}".strip()
            if normalize_string(full_name) == norm_search:
                # Now find this team in DB by abbreviation or full name
                abv = team_info.get('abv', '').upper()
                t = db.query(Team).filter(Team.sport == sport, Team.abbreviation == abv).first()
                if t:
                    return t.id
                # Fallback: search by name
                t = db.query(Team).filter(Team.sport == sport, Team.name == full_name).first()
                if t:
                    return t.id

    # 5. Match by city alone (if search contains city)
    if team_list:
        for team_info in team_list:
            city = team_info.get('city', '').strip()
            if city and normalize_string(city) in norm_search:
                abv = team_info.get('abv', '').upper()
                t = db.query(Team).filter(Team.sport == sport, Team.abbreviation == abv).first()
                if t:
                    return t.id

    # 6. Abbreviation from team_list
    if team_list:
        for team_info in team_list:
            abv = team_info.get('abv', '').lower()
            if abv and abv in norm_search:
                t = db.query(Team).filter(Team.sport == sport, Team.abbreviation == abv.upper()).first()
                if t:
                    return t.id

    # 7. Direct overrides (manual mapping)
    overrides = {
        "tarleton state texans": "Tarleton State Texans",
        "ball state cardinals": "Ball State Cardinals",
        "kansas state wildcats": "Kansas State Wildcats",
        "lsu tigers": "LSU Tigers",
        "san diego state aztecs": "San Diego State Aztecs",
        "ualbany great danes": "UAlbany Great Danes",
        "new haven chargers": "New Haven Chargers",
        "west georgia wolves": "West Georgia Wolves",
        "nc state wolfpack": "North Carolina State Wolfpack",
    }
    if norm_search in overrides:
        target_name = overrides[norm_search]
        t = db.query(Team).filter(Team.sport == sport, Team.name.ilike(target_name)).first()
        if t:
            return t.id

    # 8. Try abbreviation directly from DB
    t = db.query(Team).filter(Team.sport == sport, Team.abbreviation.ilike(search_name)).first()
    if t:
        return t.id

    return None