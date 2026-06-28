# sports/base_sport.py
from abc import ABC, abstractmethod
import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import sqlite3
import json

logger = logging.getLogger(__name__)

class BaseSport(ABC):
    """Base class for all sports"""
    
    def __init__(self, sport_name: str, api_url: str, db_path: str = "sports_data.db"):
        self.sport_name = sport_name
        self.api_url = api_url
        self.db_path = db_path
        self.client = httpx.Client(timeout=30.0)
        self._init_database()
    
    @abstractmethod
    def parse_gamelines(self, data: Dict) -> List[Dict]:
        """Parse sport-specific gameline data"""
        pass
    
    @abstractmethod
    def get_team_abbr(self, team_name: str) -> str:
        """Get team abbreviation from full name"""
        pass
    
    @abstractmethod
    async def get_team_stats(self, team: str, year: str) -> List[Dict]:
        """Get team stats from API"""
        pass
    
    def _init_database(self):
        """Initialize SQLite database for this sport"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create gamelines table if it doesn't exist
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.sport_name}_gamelines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                game_id TEXT NOT NULL,
                game_day DATE NOT NULL,
                start_time TEXT,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_abbr TEXT NOT NULL,
                away_abbr TEXT NOT NULL,
                home_ml INTEGER,
                away_ml INTEGER,
                home_spread REAL,
                away_spread REAL,
                home_spread_odds INTEGER,
                away_spread_odds INTEGER,
                total REAL,
                over_odds INTEGER,
                under_odds INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source, game_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Initialized database for {self.sport_name}")
    
    async def fetch_gamelines(self, source: str = None) -> Optional[List[Dict]]:
        """Fetch gamelines from API"""
        try:
            response = await self.client.get(f"{self.api_url}/gamelines")
            response.raise_for_status()
            data = response.json()
            
            # Parse the data
            games = self.parse_gamelines(data)
            
            # Store in database
            if games:
                self.store_gamelines(games, source or 'espn_bets')
            
            return games
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {self.sport_name} gamelines: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {self.sport_name} gamelines: {e}")
            return None
    
    def store_gamelines(self, games: List[Dict], source: str):
        """Store gamelines in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for game in games:
            try:
                cursor.execute(f'''
                    INSERT OR REPLACE INTO {self.sport_name}_gamelines 
                    (source, game_id, game_day, start_time, home_team, away_team, 
                     home_abbr, away_abbr, home_ml, away_ml, home_spread, away_spread,
                     home_spread_odds, away_spread_odds, total, over_odds, under_odds, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    source,
                    game.get('game_id', f"{self.sport_name}_{len(games)}"),
                    game.get('game_day', datetime.now().strftime('%Y-%m-%d')),
                    game.get('start_time'),
                    game.get('home_team'),
                    game.get('away_team'),
                    game.get('home_abbr'),
                    game.get('away_abbr'),
                    game.get('home_ml'),
                    game.get('away_ml'),
                    game.get('home_spread'),
                    game.get('away_spread'),
                    game.get('home_spread_odds', -110),
                    game.get('away_spread_odds', -110),
                    game.get('total'),
                    game.get('over_odds', -110),
                    game.get('under_odds', -110)
                ))
            except Exception as e:
                logger.error(f"Error storing {self.sport_name} game: {e}")
        
        conn.commit()
        conn.close()
        logger.info(f"Stored {len(games)} {self.sport_name} gamelines from {source}")
    
    def get_cached_gamelines(self, source: str = None) -> List[Dict]:
        """Get cached gamelines from database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if source:
                cursor.execute(f'''
                    SELECT * FROM {self.sport_name}_gamelines 
                    WHERE source = ? AND date(game_day) >= date('now')
                    ORDER BY game_day, start_time
                ''', (source,))
            else:
                cursor.execute(f'''
                    SELECT * FROM {self.sport_name}_gamelines 
                    WHERE date(game_day) >= date('now')
                    ORDER BY game_day, start_time
                ''')
            
            results = [dict(row) for row in cursor.fetchall()]
            return results
            
        except Exception as e:
            logger.error(f"Error reading {self.sport_name} gamelines: {e}")
            return []
        finally:
            conn.close()
    
    def delete_old_gamelines(self, days: int = 7):
        """Delete gamelines older than specified days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(f'''
                DELETE FROM {self.sport_name}_gamelines 
                WHERE date(game_day) < date('now', ?)
            ''', (f'-{days} days',))
            
            deleted = cursor.rowcount
            conn.commit()
            logger.info(f"Deleted {deleted} old {self.sport_name} gamelines")
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting {self.sport_name} gamelines: {e}")
            return 0
        finally:
            conn.close()