# managers/parlay_manager.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Tuple
import itertools
import logging
from models.parlay import Parlay, ParlayCombination

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
        # Generate all combinations
        all_combinations = list(itertools.product(*selections))
        
        # Apply win locks (must include)
        if win_locks:
            filtered = []
            for combo in all_combinations:
                if all(any(lock['team'] in selection and lock['type'] in selection for selection in combo) for lock in win_locks):
                    filtered.append(combo)
            all_combinations = filtered
        
        # Apply loss locks (must exclude)
        if loss_locks:
            filtered = []
            for combo in all_combinations:
                if not any(any(lock['team'] in selection and lock['type'] in selection for selection in combo) for lock in loss_locks):
                    filtered.append(combo)
            all_combinations = filtered
        
        return [list(combo) for combo in all_combinations]
    
    def calculate_parlay_odds(self, selections: List[str]) -> float:
        """
        Calculate parlay odds from individual selections
        """
        total_odds = 1.0
        for selection in selections:
            # Extract odds from selection string
            import re
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