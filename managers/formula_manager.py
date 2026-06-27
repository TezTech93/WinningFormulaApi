# managers/formula_manager.py
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from models.formula import UserFormula, FormulaType
import logging

logger = logging.getLogger(__name__)

class FormulaManager:
    def __init__(self, db: Session):
        self.db = db
    
    def create_formula(
        self,
        user_id: int,
        formula_name: str,
        formula: str,
        sport: str,
        formula_type: str = "ranking",
        description: str = None
    ) -> UserFormula:
        new_formula = UserFormula(
            user_id=user_id,
            formula_name=formula_name,
            formula=formula,
            sport=sport,
            formula_type=FormulaType(formula_type),
            description=description
        )
        self.db.add(new_formula)
        self.db.commit()
        self.db.refresh(new_formula)
        return new_formula
    
    def get_user_formulas(self, user_id: int) -> List[UserFormula]:
        return self.db.query(UserFormula).filter(
            UserFormula.user_id == user_id
        ).order_by(UserFormula.created_at.desc()).all()
    
    def get_formula_by_id(self, formula_id: int, user_id: int) -> Optional[UserFormula]:
        return self.db.query(UserFormula).filter(
            UserFormula.id == formula_id,
            UserFormula.user_id == user_id
        ).first()
    
    def delete_formula(self, formula_id: int, user_id: int) -> bool:
        formula = self.get_formula_by_id(formula_id, user_id)
        if not formula:
            return False
        self.db.delete(formula)
        self.db.commit()
        return True
    
    def update_formula(
        self,
        formula_id: int,
        user_id: int,
        formula_name: str = None,
        formula: str = None,
        description: str = None
    ) -> Optional[UserFormula]:
        formula = self.get_formula_by_id(formula_id, user_id)
        if not formula:
            return None
        
        if formula_name:
            formula.formula_name = formula_name
        if formula:
            formula.formula = formula
        if description:
            formula.description = description
        
        self.db.commit()
        self.db.refresh(formula)
        return formula
    
    def update_accuracy_score(self, formula_id: int, user_id: int, score: int) -> bool:
        formula = self.get_formula_by_id(formula_id, user_id)
        if not formula:
            return False
        formula.accuracy_score = score
        formula.simulation_count += 1
        self.db.commit()
        return True