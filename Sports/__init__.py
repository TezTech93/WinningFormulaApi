from Sports.manager import SportsManager, sports_manager
from Sports.base_scraper import BaseSportScraper

from Sports.nfl.scraper import NFLScraper
from Sports.nba.scraper import NBAScraper
from Sports.mlb.scraper import MLBScraper
from Sports.nhl.scraper import NHLScraper
from Sports.ncaaf.scraper import NCAAFScraper
from Sports.ncaab.scraper import NCAABScraper

__all__ = [
    'SportsManager',
    'sports_manager',
    'BaseSportScraper',
    'NFLScraper',
    'NBAScraper',
    'MLBScraper',
    'NHLScraper',
    'NCAAFScraper',
    'NCAABScraper',
    'SUPPORTED_SPORTS'
]

# Convenience variable
SUPPORTED_SPORTS = ['nfl', 'nba', 'mlb', 'nhl', 'ncaaf', 'ncaab']