# utils/team_resolver.py
import unicodedata
from sqlalchemy.orm import Session
from models.team import Team

def normalize_string(s: str) -> str:
    """Remove accents, convert to lowercase, strip extra spaces."""
    s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8')
    return s.lower().strip()

def get_team_id(sport: str, search_name: str, db: Session, team_list=None) -> int:
    if not search_name:
        return None

    norm_search = normalize_string(search_name)
    
    # --- Build mapping from full name to abbreviation (using team_list) ---
    name_to_abbr = {}
    if team_list:
        for team in team_list:
            city = team.get('city', '').strip()
            tname = team.get('teamName', '').strip()
            abv = team.get('abv', '').upper()
            if city and tname:
                full = normalize_string(f"{city} {tname}")
                name_to_abbr[full] = abv
            # Also map by just teamName (for cases like "LSU Tigers")
            if tname:
                name_to_abbr[normalize_string(tname)] = abv

    # 1. Try to find by abbreviation via the mapping
    if norm_search in name_to_abbr:
        abv = name_to_abbr[norm_search]
        team = db.query(Team).filter(Team.sport == sport, Team.abbreviation == abv).first()
        if team:
            return team.id

    # 2. Hardcoded overrides for specific mismatches
    overrides = {
        "tarleton state texans": "TAR",
        "ball state cardinals": "BALL",
        "kansas state wildcats": "KSU",
        "lsu tigers": "LSU",
        "san diego state aztecs": "SDSU",
        "ualbany great danes": "UALB",
        "new haven chargers": "NEWH",
        "west georgia wolves": "UWG",
        "nc state wolfpack": "NCST",
    }
    if norm_search in overrides:
        abv = overrides[norm_search]
        team = db.query(Team).filter(Team.sport == sport, Team.abbreviation == abv).first()
        if team:
            return team.id

    # 3. Try exact DB name (case-insensitive)
    team = db.query(Team).filter(Team.sport == sport, Team.name.ilike(search_name)).first()
    if team:
        return team.id

    # 4. Try normalized DB name
    teams = db.query(Team).filter(Team.sport == sport).all()
    for t in teams:
        if normalize_string(t.name) == norm_search:
            return t.id

    # 5. Partial match (substring)
    for t in teams:
        t_norm = normalize_string(t.name)
        if norm_search in t_norm or t_norm in norm_search:
            return t.id

    # 6. Try abbreviation directly from DB
    team = db.query(Team).filter(Team.sport == sport, Team.abbreviation.ilike(search_name)).first()
    if team:
        return team.id

    return None