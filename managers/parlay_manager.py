# managers/parlay_manager.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
import itertools
import logging
import re

logger = logging.getLogger(__name__)

class ParlayManager:
    def __init__(self, db: Session):
        self.db = db
    
    def generate_combinations(
        self,
        selections: List[List[str]],
        win_locks: List[Dict] = None,
        loss_locks: List[Dict] = None
    ) -> List[List[str]]:
        """
        Generate all possible parlay combinations with optional locks
        """
        # Generate all combinations using itertools.product
        all_combinations = list(itertools.product(*selections))
        
        # Apply win locks (must include)
        if win_locks:
            filtered = []
            for combo in all_combinations:
                # Check if all win locks are included
                all_locks_included = True
                for lock in win_locks:
                    lock_found = False
                    for selection in combo:
                        if lock.get('team') in selection and lock.get('type') in selection:
                            lock_found = True
                            break
                    if not lock_found:
                        all_locks_included = False
                        break
                if all_locks_included:
                    filtered.append(combo)
            all_combinations = filtered
        
        # Apply loss locks (must exclude)
        if loss_locks:
            filtered = []
            for combo in all_combinations:
                # Check if any loss locks are included
                any_lock_included = False
                for lock in loss_locks:
                    for selection in combo:
                        if lock.get('team') in selection and lock.get('type') in selection:
                            any_lock_included = True
                            break
                    if any_lock_included:
                        break
                if not any_lock_included:
                    filtered.append(combo)
            all_combinations = filtered
        
        return [list(combo) for combo in all_combinations]
    
    def calculate_parlay_odds(self, selections: List[str]) -> float:
        """
        Calculate parlay odds from individual selections
        """
        total_odds = 1.0
        
        for selection in selections:
            # Extract odds from selection string (e.g., "Team +150" -> 150)
            odds_match = re.search(r'[+-]?\d+(\.\d+)?', selection)
            if odds_match:
                odds = float(odds_match.group())
                if odds > 0:
                    total_odds *= (1 + odds / 100)
                else:
                    total_odds *= (1 + 100 / abs(odds))
        
        return round(total_odds, 2)
    
    def calculate_payout(self, bet_amount: float, selections: List[str]) -> Dict[str, float]:
        """
        Calculate payout and profit for a parlay
        """
        total_odds = self.calculate_parlay_odds(selections)
        payout = bet_amount * total_odds
        profit = payout - bet_amount
        
        return {
            'total_odds': total_odds,
            'payout': round(payout, 2),
            'profit': round(profit, 2)
        }
    
    def get_parlay_by_id(self, parlay_id: int, user_id: int) -> Optional[Dict]:
        """Get a parlay by ID"""
        from models.parlay import Parlay
        
        parlay = self.db.query(Parlay).filter(
            Parlay.id == parlay_id,
            Parlay.user_id == user_id
        ).first()
        
        if not parlay:
            return None
        
        return {
            'id': parlay.id,
            'user_id': parlay.user_id,
            'sport': parlay.sport,
            'name': parlay.name,
            'bet_amount': parlay.bet_amount,
            'total_odds': parlay.total_odds,
            'potential_payout': parlay.potential_payout,
            'potential_profit': parlay.potential_profit,
            'status': parlay.status.value if parlay.status else None,
            'selections_count': parlay.selections_count,
            'extra_data': parlay.extra_data,
            'created_at': parlay.created_at.isoformat() if parlay.created_at else None,
            'updated_at': parlay.updated_at.isoformat() if parlay.updated_at else None
        }
    
    def get_user_parlays(self, user_id: int, sport: str = None, status: str = None) -> List[Dict]:
        """Get all parlays for a user"""
        from models.parlay import Parlay
        
        query = self.db.query(Parlay).filter(Parlay.user_id == user_id)
        
        if sport:
            query = query.filter(Parlay.sport == sport)
        if status:
            query = query.filter(Parlay.status == status)
        
        parlays = query.order_by(Parlay.created_at.desc()).all()
        
        return [{
            'id': p.id,
            'user_id': p.user_id,
            'sport': p.sport,
            'name': p.name,
            'bet_amount': p.bet_amount,
            'total_odds': p.total_odds,
            'potential_payout': p.potential_payout,
            'potential_profit': p.potential_profit,
            'status': p.status.value if p.status else None,
            'selections_count': p.selections_count,
            'created_at': p.created_at.isoformat() if p.created_at else None,
            'updated_at': p.updated_at.isoformat() if p.updated_at else None
        } for p in parlays]
    
    def update_parlay_status(self, parlay_id: int, user_id: int, status: str) -> bool:
        """Update a parlay's status"""
        from models.parlay import Parlay, ParlayStatus
        
        parlay = self.db.query(Parlay).filter(
            Parlay.id == parlay_id,
            Parlay.user_id == user_id
        ).first()
        
        if not parlay:
            return False
        
        parlay.status = ParlayStatus(status)
        self.db.commit()
        self.db.refresh(parlay)
        return True
    
    def delete_parlay(self, parlay_id: int, user_id: int) -> bool:
        """Delete a parlay"""
        from models.parlay import Parlay
        
        parlay = self.db.query(Parlay).filter(
            Parlay.id == parlay_id,
            Parlay.user_id == user_id
        ).first()
        
        if not parlay:
            return False
        
        self.db.delete(parlay)
        self.db.commit()
        return True