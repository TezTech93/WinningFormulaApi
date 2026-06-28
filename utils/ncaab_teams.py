# utils/ncaab_teams.py
# Complete list of all Division I NCAAB teams

NCAAB_TEAMS = [
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
    {"name": "Notre Dame Fighting Irish", "abbr": "ND", "conference": "ACC"},
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

    # === Big East ===
    {"name": "Butler Bulldogs", "abbr": "BUT", "conference": "Big East"},
    {"name": "Creighton Bluejays", "abbr": "CREI", "conference": "Big East"},
    {"name": "DePaul Blue Demons", "abbr": "DEP", "conference": "Big East"},
    {"name": "Georgetown Hoyas", "abbr": "GTWN", "conference": "Big East"},
    {"name": "Marquette Golden Eagles", "abbr": "MARQ", "conference": "Big East"},
    {"name": "Providence Friars", "abbr": "PROV", "conference": "Big East"},
    {"name": "St. John's Red Storm", "abbr": "SJU", "conference": "Big East"},
    {"name": "Seton Hall Pirates", "abbr": "SHU", "conference": "Big East"},
    {"name": "UConn Huskies", "abbr": "CONN", "conference": "Big East"},
    {"name": "Villanova Wildcats", "abbr": "VILL", "conference": "Big East"},
    {"name": "Xavier Musketeers", "abbr": "XAV", "conference": "Big East"},

    # === Atlantic 10 (A-10) ===
    {"name": "Davidson Wildcats", "abbr": "DAV", "conference": "A-10"},
    {"name": "Dayton Flyers", "abbr": "DAY", "conference": "A-10"},
    {"name": "Duquesne Dukes", "abbr": "DUQ", "conference": "A-10"},
    {"name": "Fordham Rams", "abbr": "FOR", "conference": "A-10"},
    {"name": "George Mason Patriots", "abbr": "GMU", "conference": "A-10"},
    {"name": "George Washington Colonials", "abbr": "GW", "conference": "A-10"},
    {"name": "La Salle Explorers", "abbr": "LAS", "conference": "A-10"},
    {"name": "Loyola Chicago Ramblers", "abbr": "LUC", "conference": "A-10"},
    {"name": "Rhode Island Rams", "abbr": "URI", "conference": "A-10"},
    {"name": "Richmond Spiders", "abbr": "RICH", "conference": "A-10"},
    {"name": "St. Bonaventure Bonnies", "abbr": "SBU", "conference": "A-10"},
    {"name": "St. Joseph's Hawks", "abbr": "SJU", "conference": "A-10"},
    {"name": "St. Louis Billikens", "abbr": "SLU", "conference": "A-10"},
    {"name": "VCU Rams", "abbr": "VCU", "conference": "A-10"},

    # === American Athletic Conference (AAC) ===
    {"name": "Charlotte 49ers", "abbr": "CLT", "conference": "AAC"},
    {"name": "East Carolina Pirates", "abbr": "ECU", "conference": "AAC"},
    {"name": "Florida Atlantic Owls", "abbr": "FAU", "conference": "AAC"},
    {"name": "Memphis Tigers", "abbr": "MEM", "conference": "AAC"},
    {"name": "North Texas Mean Green", "abbr": "UNT", "conference": "AAC"},
    {"name": "Rice Owls", "abbr": "RICE", "conference": "AAC"},
    {"name": "South Florida Bulls", "abbr": "USF", "conference": "AAC"},
    {"name": "Temple Owls", "abbr": "TEM", "conference": "AAC"},
    {"name": "Tulane Green Wave", "abbr": "TULN", "conference": "AAC"},
    {"name": "Tulsa Golden Hurricane", "abbr": "TLSA", "conference": "AAC"},
    {"name": "UAB Blazers", "abbr": "UAB", "conference": "AAC"},
    {"name": "UTSA Roadrunners", "abbr": "UTSA", "conference": "AAC"},
    {"name": "Wichita State Shockers", "abbr": "WICH", "conference": "AAC"},

    # === Mountain West ===
    {"name": "Air Force Falcons", "abbr": "AFA", "conference": "Mountain West"},
    {"name": "Boise State Broncos", "abbr": "BSU", "conference": "Mountain West"},
    {"name": "Colorado State Rams", "abbr": "CSU", "conference": "Mountain West"},
    {"name": "Fresno State Bulldogs", "abbr": "FRES", "conference": "Mountain West"},
    {"name": "Nevada Wolf Pack", "abbr": "NEV", "conference": "Mountain West"},
    {"name": "New Mexico Lobos", "abbr": "NM", "conference": "Mountain West"},
    {"name": "San Diego State Aztecs", "abbr": "SDSU", "conference": "Mountain West"},
    {"name": "San Jose State Spartans", "abbr": "SJSU", "conference": "Mountain West"},
    {"name": "UNLV Rebels", "abbr": "UNLV", "conference": "Mountain West"},
    {"name": "Utah State Aggies", "abbr": "USU", "conference": "Mountain West"},
    {"name": "Wyoming Cowboys", "abbr": "WYO", "conference": "Mountain West"},

    # === West Coast Conference (WCC) ===
    {"name": "Gonzaga Bulldogs", "abbr": "GONZ", "conference": "WCC"},
    {"name": "Loyola Marymount Lions", "abbr": "LMU", "conference": "WCC"},
    {"name": "Pacific Tigers", "abbr": "PAC", "conference": "WCC"},
    {"name": "Pepperdine Waves", "abbr": "PEPP", "conference": "WCC"},
    {"name": "Portland Pilots", "abbr": "PORT", "conference": "WCC"},
    {"name": "Saint Mary's Gaels", "abbr": "SMC", "conference": "WCC"},
    {"name": "San Diego Toreros", "abbr": "USD", "conference": "WCC"},
    {"name": "San Francisco Dons", "abbr": "SF", "conference": "WCC"},
    {"name": "Santa Clara Broncos", "abbr": "SCU", "conference": "WCC"},

    # === Missouri Valley Conference (MVC) ===
    {"name": "Belmont Bruins", "abbr": "BEL", "conference": "MVC"},
    {"name": "Bradley Braves", "abbr": "BRAD", "conference": "MVC"},
    {"name": "Drake Bulldogs", "abbr": "DRKE", "conference": "MVC"},
    {"name": "Evansville Purple Aces", "abbr": "EVAN", "conference": "MVC"},
    {"name": "Illinois State Redbirds", "abbr": "ILST", "conference": "MVC"},
    {"name": "Indiana State Sycamores", "abbr": "INST", "conference": "MVC"},
    {"name": "Missouri State Bears", "abbr": "MOSU", "conference": "MVC"},
    {"name": "Murray State Racers", "abbr": "MURR", "conference": "MVC"},
    {"name": "Northern Iowa Panthers", "abbr": "UNI", "conference": "MVC"},
    {"name": "Southern Illinois Salukis", "abbr": "SIU", "conference": "MVC"},
    {"name": "UIC Flames", "abbr": "UIC", "conference": "MVC"},
    {"name": "Valparaiso Beacons", "abbr": "VAL", "conference": "MVC"},

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

    # === MAC ===
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

    # === Sun Belt ===
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

    # === Ivy League ===
    {"name": "Brown Bears", "abbr": "BRWN", "conference": "Ivy"},
    {"name": "Columbia Lions", "abbr": "COL", "conference": "Ivy"},
    {"name": "Cornell Big Red", "abbr": "COR", "conference": "Ivy"},
    {"name": "Dartmouth Big Green", "abbr": "DART", "conference": "Ivy"},
    {"name": "Harvard Crimson", "abbr": "HARV", "conference": "Ivy"},
    {"name": "Penn Quakers", "abbr": "PENN", "conference": "Ivy"},
    {"name": "Princeton Tigers", "abbr": "PRIN", "conference": "Ivy"},
    {"name": "Yale Bulldogs", "abbr": "YALE", "conference": "Ivy"},

    # === Independents ===
    {"name": "Chicago State Cougars", "abbr": "CHST", "conference": "Independent"},
    {"name": "Hartford Hawks", "abbr": "HART", "conference": "Independent"},
    {"name": "Long Island Sharks", "abbr": "LIU", "conference": "Independent"},
    {"name": "Merrimack Warriors", "abbr": "MERR", "conference": "Independent"},
    {"name": "Stonehill Skyhawks", "abbr": "STON", "conference": "Independent"},
]

def get_ncaab_teams():
    return NCAAB_TEAMS

def get_ncaab_teams_by_conference(conference: str):
    return [t for t in NCAAB_TEAMS if t['conference'] == conference]

def get_ncaab_team_by_abbr(abbr: str):
    for team in NCAAB_TEAMS:
        if team['abbr'] == abbr:
            return team
    return None

def get_ncaab_conferences():
    return list(set(t['conference'] for t in NCAAB_TEAMS))