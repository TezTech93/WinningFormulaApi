# utils/ncaaf_teams.py
# Complete list of all FBS NCAAF teams

NCAAF_TEAMS = [
    # === ACC ===
    {"name": "Boston College Eagles", "abbr": "BC", "conference": "ACC"},
    {"name": "Clemson Tigers", "abbr": "CLEM", "conference": "ACC"},
    {"name": "Duke Blue Devils", "abbr": "DUKE", "conference": "ACC"},
    {"name": "Florida State Seminoles", "abbr": "FSU", "conference": "ACC"},
    {"name": "Georgia Tech Yellow Jackets", "abbr": "GT", "conference": "ACC"},
    {"name": "Louisville Cardinals", "abbr": "LOU", "conference": "ACC"},
    {"name": "Miami Hurricanes", "abbr": "MIA", "conference": "ACC"},
    {"name": "NC State Wolfpack", "abbr": "NCST", "conference": "ACC"},
    {"name": "North Carolina Tar Heels", "abbr": "UNC", "conference": "ACC"},
    {"name": "Pittsburgh Panthers", "abbr": "PITT", "conference": "ACC"},
    {"name": "Syracuse Orange", "abbr": "SYR", "conference": "ACC"},
    {"name": "Virginia Cavaliers", "abbr": "UVA", "conference": "ACC"},
    {"name": "Virginia Tech Hokies", "abbr": "VT", "conference": "ACC"},
    {"name": "Wake Forest Demon Deacons", "abbr": "WAKE", "conference": "ACC"},
    {"name": "California Golden Bears", "abbr": "CAL", "conference": "ACC"},
    {"name": "Stanford Cardinal", "abbr": "STAN", "conference": "ACC"},
    {"name": "SMU Mustangs", "abbr": "SMU", "conference": "ACC"},

    # === Big Ten ===
    {"name": "Illinois Fighting Illini", "abbr": "ILL", "conference": "Big Ten"},
    {"name": "Indiana Hoosiers", "abbr": "IND", "conference": "Big Ten"},
    {"name": "Iowa Hawkeyes", "abbr": "IOWA", "conference": "Big Ten"},
    {"name": "Maryland Terrapins", "abbr": "MD", "conference": "Big Ten"},
    {"name": "Michigan Wolverines", "abbr": "MICH", "conference": "Big Ten"},
    {"name": "Michigan State Spartans", "abbr": "MSU", "conference": "Big Ten"},
    {"name": "Minnesota Golden Gophers", "abbr": "MINN", "conference": "Big Ten"},
    {"name": "Nebraska Cornhuskers", "abbr": "NEB", "conference": "Big Ten"},
    {"name": "Northwestern Wildcats", "abbr": "NW", "conference": "Big Ten"},
    {"name": "Ohio State Buckeyes", "abbr": "OSU", "conference": "Big Ten"},
    {"name": "Oregon Ducks", "abbr": "ORE", "conference": "Big Ten"},
    {"name": "Penn State Nittany Lions", "abbr": "PSU", "conference": "Big Ten"},
    {"name": "Purdue Boilermakers", "abbr": "PUR", "conference": "Big Ten"},
    {"name": "Rutgers Scarlet Knights", "abbr": "RUTG", "conference": "Big Ten"},
    {"name": "UCLA Bruins", "abbr": "UCLA", "conference": "Big Ten"},
    {"name": "USC Trojans", "abbr": "USC", "conference": "Big Ten"},
    {"name": "Washington Huskies", "abbr": "WASH", "conference": "Big Ten"},
    {"name": "Wisconsin Badgers", "abbr": "WIS", "conference": "Big Ten"},

    # === Big 12 ===
    {"name": "Arizona Wildcats", "abbr": "ARIZ", "conference": "Big 12"},
    {"name": "Arizona State Sun Devils", "abbr": "ASU", "conference": "Big 12"},
    {"name": "Baylor Bears", "abbr": "BAY", "conference": "Big 12"},
    {"name": "BYU Cougars", "abbr": "BYU", "conference": "Big 12"},
    {"name": "Cincinnati Bearcats", "abbr": "CIN", "conference": "Big 12"},
    {"name": "Colorado Buffaloes", "abbr": "COLO", "conference": "Big 12"},
    {"name": "Houston Cougars", "abbr": "HOU", "conference": "Big 12"},
    {"name": "Iowa State Cyclones", "abbr": "ISU", "conference": "Big 12"},
    {"name": "Kansas Jayhawks", "abbr": "KU", "conference": "Big 12"},
    {"name": "Kansas State Wildcats", "abbr": "KSU", "conference": "Big 12"},
    {"name": "Oklahoma Sooners", "abbr": "OKLA", "conference": "Big 12"},
    {"name": "Oklahoma State Cowboys", "abbr": "OKST", "conference": "Big 12"},
    {"name": "TCU Horned Frogs", "abbr": "TCU", "conference": "Big 12"},
    {"name": "Texas Tech Red Raiders", "abbr": "TTU", "conference": "Big 12"},
    {"name": "UCF Knights", "abbr": "UCF", "conference": "Big 12"},
    {"name": "Utah Utes", "abbr": "UTAH", "conference": "Big 12"},
    {"name": "West Virginia Mountaineers", "abbr": "WVU", "conference": "Big 12"},

    # === SEC ===
    {"name": "Alabama Crimson Tide", "abbr": "ALA", "conference": "SEC"},
    {"name": "Arkansas Razorbacks", "abbr": "ARK", "conference": "SEC"},
    {"name": "Auburn Tigers", "abbr": "AUB", "conference": "SEC"},
    {"name": "Florida Gators", "abbr": "FLA", "conference": "SEC"},
    {"name": "Georgia Bulldogs", "abbr": "UGA", "conference": "SEC"},
    {"name": "Kentucky Wildcats", "abbr": "UK", "conference": "SEC"},
    {"name": "LSU Tigers", "abbr": "LSU", "conference": "SEC"},
    {"name": "Mississippi State Bulldogs", "abbr": "MSST", "conference": "SEC"},
    {"name": "Missouri Tigers", "abbr": "MIZZ", "conference": "SEC"},
    {"name": "Ole Miss Rebels", "abbr": "MISS", "conference": "SEC"},
    {"name": "South Carolina Gamecocks", "abbr": "SCAR", "conference": "SEC"},
    {"name": "Tennessee Volunteers", "abbr": "TENN", "conference": "SEC"},
    {"name": "Texas Longhorns", "abbr": "TEX", "conference": "SEC"},
    {"name": "Texas A&M Aggies", "abbr": "TAMU", "conference": "SEC"},
    {"name": "Vanderbilt Commodores", "abbr": "VANDY", "conference": "SEC"},

    # === American Athletic Conference (AAC) ===
    {"name": "Army Black Knights", "abbr": "ARMY", "conference": "AAC"},
    {"name": "Charlotte 49ers", "abbr": "CLT", "conference": "AAC"},
    {"name": "East Carolina Pirates", "abbr": "ECU", "conference": "AAC"},
    {"name": "Florida Atlantic Owls", "abbr": "FAU", "conference": "AAC"},
    {"name": "Memphis Tigers", "abbr": "MEM", "conference": "AAC"},
    {"name": "Navy Midshipmen", "abbr": "NAVY", "conference": "AAC"},
    {"name": "North Texas Mean Green", "abbr": "UNT", "conference": "AAC"},
    {"name": "Rice Owls", "abbr": "RICE", "conference": "AAC"},
    {"name": "South Florida Bulls", "abbr": "USF", "conference": "AAC"},
    {"name": "Temple Owls", "abbr": "TEM", "conference": "AAC"},
    {"name": "Tulane Green Wave", "abbr": "TULN", "conference": "AAC"},
    {"name": "Tulsa Golden Hurricane", "abbr": "TLSA", "conference": "AAC"},
    {"name": "UAB Blazers", "abbr": "UAB", "conference": "AAC"},
    {"name": "UTSA Roadrunners", "abbr": "UTSA", "conference": "AAC"},

    # === Conference USA (C-USA) ===
    {"name": "FIU Panthers", "abbr": "FIU", "conference": "C-USA"},
    {"name": "Jacksonville State Gamecocks", "abbr": "JVST", "conference": "C-USA"},
    {"name": "Kennesaw State Owls", "abbr": "KENN", "conference": "C-USA"},
    {"name": "Liberty Flames", "abbr": "LIB", "conference": "C-USA"},
    {"name": "Louisiana Tech Bulldogs", "abbr": "LT", "conference": "C-USA"},
    {"name": "Middle Tennessee Blue Raiders", "abbr": "MTSU", "conference": "C-USA"},
    {"name": "New Mexico State Aggies", "abbr": "NMSU", "conference": "C-USA"},
    {"name": "Sam Houston Bearkats", "abbr": "SHSU", "conference": "C-USA"},
    {"name": "UTEP Miners", "abbr": "UTEP", "conference": "C-USA"},
    {"name": "Western Kentucky Hilltoppers", "abbr": "WKU", "conference": "C-USA"},

    # === Mid-American Conference (MAC) ===
    {"name": "Akron Zips", "abbr": "AKR", "conference": "MAC"},
    {"name": "Ball State Cardinals", "abbr": "BALL", "conference": "MAC"},
    {"name": "Bowling Green Falcons", "abbr": "BGSU", "conference": "MAC"},
    {"name": "Buffalo Bulls", "abbr": "BUFF", "conference": "MAC"},
    {"name": "Central Michigan Chippewas", "abbr": "CMU", "conference": "MAC"},
    {"name": "Eastern Michigan Eagles", "abbr": "EMU", "conference": "MAC"},
    {"name": "Kent State Golden Flashes", "abbr": "KENT", "conference": "MAC"},
    {"name": "Miami RedHawks", "abbr": "MIAOH", "conference": "MAC"},
    {"name": "Northern Illinois Huskies", "abbr": "NIU", "conference": "MAC"},
    {"name": "Ohio Bobcats", "abbr": "OHIO", "conference": "MAC"},
    {"name": "Toledo Rockets", "abbr": "TOL", "conference": "MAC"},
    {"name": "Western Michigan Broncos", "abbr": "WMU", "conference": "MAC"},

    # === Mountain West Conference (MWC) ===
    {"name": "Air Force Falcons", "abbr": "AFA", "conference": "Mountain West"},
    {"name": "Boise State Broncos", "abbr": "BSU", "conference": "Mountain West"},
    {"name": "Colorado State Rams", "abbr": "CSU", "conference": "Mountain West"},
    {"name": "Fresno State Bulldogs", "abbr": "FRES", "conference": "Mountain West"},
    {"name": "Hawaii Rainbow Warriors", "abbr": "HAW", "conference": "Mountain West"},
    {"name": "Nevada Wolf Pack", "abbr": "NEV", "conference": "Mountain West"},
    {"name": "New Mexico Lobos", "abbr": "NM", "conference": "Mountain West"},
    {"name": "San Diego State Aztecs", "abbr": "SDSU", "conference": "Mountain West"},
    {"name": "San Jose State Spartans", "abbr": "SJSU", "conference": "Mountain West"},
    {"name": "UNLV Rebels", "abbr": "UNLV", "conference": "Mountain West"},
    {"name": "Utah State Aggies", "abbr": "USU", "conference": "Mountain West"},
    {"name": "Wyoming Cowboys", "abbr": "WYO", "conference": "Mountain West"},

    # === Sun Belt Conference ===
    {"name": "Appalachian State Mountaineers", "abbr": "APP", "conference": "Sun Belt"},
    {"name": "Arkansas State Red Wolves", "abbr": "ARST", "conference": "Sun Belt"},
    {"name": "Coastal Carolina Chanticleers", "abbr": "CCU", "conference": "Sun Belt"},
    {"name": "Georgia Southern Eagles", "abbr": "GASO", "conference": "Sun Belt"},
    {"name": "Georgia State Panthers", "abbr": "GAST", "conference": "Sun Belt"},
    {"name": "James Madison Dukes", "abbr": "JMU", "conference": "Sun Belt"},
    {"name": "Louisiana Ragin' Cajuns", "abbr": "ULL", "conference": "Sun Belt"},
    {"name": "Louisiana-Monroe Warhawks", "abbr": "ULM", "conference": "Sun Belt"},
    {"name": "Marshall Thundering Herd", "abbr": "MRSH", "conference": "Sun Belt"},
    {"name": "Old Dominion Monarchs", "abbr": "ODU", "conference": "Sun Belt"},
    {"name": "South Alabama Jaguars", "abbr": "USA", "conference": "Sun Belt"},
    {"name": "Southern Miss Golden Eagles", "abbr": "USM", "conference": "Sun Belt"},
    {"name": "Texas State Bobcats", "abbr": "TXST", "conference": "Sun Belt"},
    {"name": "Troy Trojans", "abbr": "TROY", "conference": "Sun Belt"},

    # === Independents ===
    {"name": "Notre Dame Fighting Irish", "abbr": "ND", "conference": "Independent"},
    {"name": "UConn Huskies", "abbr": "CONN", "conference": "Independent"},
    {"name": "UMass Minutemen", "abbr": "UMASS", "conference": "Independent"},
]

def get_ncaaf_teams():
    return NCAAF_TEAMS

def get_ncaaf_teams_by_conference(conference: str):
    return [t for t in NCAAF_TEAMS if t['conference'] == conference]

def get_ncaaf_team_by_abbr(abbr: str):
    for team in NCAAF_TEAMS:
        if team['abbr'] == abbr:
            return team
    return None

def get_ncaaf_conferences():
    return list(set(t['conference'] for t in NCAAF_TEAMS))