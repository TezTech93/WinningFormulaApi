# sports/base_scraper.py
import requests
from bs4 import BeautifulSoup
import datetime as dt
import logging
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseSportScraper(ABC):
    """Base class for sport-specific web scrapers"""
    
    def __init__(self, sport: str):
        self.sport = sport
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_soup(self, url: str) -> BeautifulSoup:
        """Fetch and parse HTML from URL"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    @abstractmethod
    def get_gamelines(self) -> List[Dict[str, Any]]:
        """Fetch gamelines for the sport"""
        pass
    
    @abstractmethod
    def get_team_stats(self, team: str, year: str) -> List[Dict[str, Any]]:
        """Fetch team stats for the sport"""
        pass
    
    @abstractmethod
    def get_season_phase(self) -> Dict[str, Any]:
        """Get current season phase (offseason, preseason, regular, playoffs, etc.)"""
        pass
    
    @abstractmethod
    def get_team_abbr(self, team_name: str) -> str:
        """Get team abbreviation from full name"""
        pass