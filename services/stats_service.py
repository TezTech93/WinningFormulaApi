# services/stats_service.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from models.team import Team, TeamStats
from models.gameline import Gameline

logger = logging.getLogger(__name__)

class StatsService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_team_stats_by_season(self, team_id: int, year: int) -> Optional[Dict]:
        """Get team stats for a specific season"""
        stats = self.db.query(TeamStats).filter(
            TeamStats.team_id == team_id,
            TeamStats.year == year
        ).first()
        
        if stats:
            return stats.stats
        return None
    
    def get_team_stats_by_range(self, team_id: int, start_year: int, end_year: int) -> List[Dict]:
        """Get team stats for a range of seasons"""
        stats = self.db.query(TeamStats).filter(
            TeamStats.team_id == team_id,
            TeamStats.year.between(start_year, end_year)
        ).order_by(TeamStats.year).all()
        
        return [s.stats for s in stats]
    
    def get_team_recent_performance(self, team_id: int, num_games: int = 5) -> List[Dict]:
        """Get a team's performance from the last X games"""
        gamelines = self.db.query(Gameline).filter(
            (Gameline.home_team_id == team_id) | (Gameline.away_team_id == team_id),
            Gameline.is_completed == True
        ).order_by(Gameline.game_date.desc()).limit(num_games).all()
        
        results = []
        for game in gamelines:
            is_home = game.home_team_id == team_id
            team_score = game.home_score if is_home else game.away_score
            opp_score = game.away_score if is_home else game.home_score
            opponent = game.away_abbr if is_home else game.home_abbr
            
            results.append({
                'date': game.game_date.isoformat(),
                'opponent': opponent,
                'location': 'Home' if is_home else 'Away',
                'result': 'W' if team_score > opp_score else 'L',
                'team_score': team_score,
                'opponent_score': opp_score,
                'margin': team_score - opp_score,
                'total': team_score + opp_score,
                'spread_covered': self._did_cover_spread(game, team_id, is_home)
            })
        
        return results
    
    def _did_cover_spread(self, game: Gameline, team_id: int, is_home: bool) -> bool:
        """Check if a team covered the spread"""
        if not game.home_spread or game.home_score is None:
            return False
        
        # For home team, home_spread is negative if favored
        # For away team, home_spread is the number they need to cover
        if is_home:
            adjusted_score = game.home_score + game.home_spread
            return adjusted_score > game.away_score
        else:
            adjusted_score = game.away_score - game.home_spread
            return adjusted_score > game.home_score
    
    def get_team_trends(self, team_id: int, num_games: int = 10) -> Dict:
        """Get team trends from recent games"""
        recent = self.get_team_recent_performance(team_id, num_games)
        
        if not recent:
            return {}
        
        wins = sum(1 for g in recent if g['result'] == 'W')
        total = len(recent)
        
        # Calculate averages
        avg_points = sum(g['team_score'] for g in recent) / total
        avg_opp_points = sum(g['opponent_score'] for g in recent) / total
        avg_margin = sum(g['margin'] for g in recent) / total
        
        return {
            'last_n_games': total,
            'wins': wins,
            'losses': total - wins,
            'win_percentage': wins / total if total > 0 else 0,
            'avg_points_for': avg_points,
            'avg_points_against': avg_opp_points,
            'avg_margin': avg_margin,
            'current_streak': self._get_current_streak(recent),
            'home_record': self._get_record_by_location(recent, 'Home'),
            'away_record': self._get_record_by_location(recent, 'Away'),
            'spread_record': self._get_spread_record(recent),
            'over_under_record': self._get_over_under_record(recent)
        }
    
    def _get_current_streak(self, games: List[Dict]) -> Dict:
        """Get current win/loss streak"""
        if not games:
            return {'type': 'None', 'length': 0}
        
        streak = 0
        result = games[0]['result']
        for game in games:
            if game['result'] == result:
                streak += 1
            else:
                break
        
        return {
            'type': 'W' if result == 'W' else 'L',
            'length': streak
        }
    
    def _get_record_by_location(self, games: List[Dict], location: str) -> Dict:
        """Get record by home/away"""
        filtered = [g for g in games if g['location'] == location]
        if not filtered:
            return {'wins': 0, 'losses': 0}
        
        wins = sum(1 for g in filtered if g['result'] == 'W')
        return {
            'wins': wins,
            'losses': len(filtered) - wins
        }
    
    def _get_spread_record(self, games: List[Dict]) -> Dict:
        """Get record against the spread"""
        covered = sum(1 for g in games if g.get('spread_covered', False))
        return {
            'covered': covered,
            'missed': len(games) - covered
        }
    
    def _get_over_under_record(self, games: List[Dict]) -> Dict:
        """Get over/under record"""
        overs = sum(1 for g in games if g.get('total', 0) > 0)
        return {
            'over': overs,
            'under': len(games) - overs
        }

class PlayerStatsService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_player_recent_games(self, player_id: int, num_games: int = 5) -> List[Dict]:
        """Get a player's stats from the last X games"""
        # This would integrate with your player stats database
        pass
    
    def get_player_trends(self, player_id: int, num_games: int = 10) -> Dict:
        """Get player trends from recent games"""
        pass

class CoachStatsService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_coach_record(self, coach_id: int) -> Dict:
        """Get coach's win/loss record"""
        pass
    
    def get_coach_head_to_head(self, coach1_id: int, coach2_id: int) -> Dict:
        """Get head-to-head record between two coaches"""
        pass