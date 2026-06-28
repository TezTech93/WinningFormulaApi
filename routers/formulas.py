# routers/formulas.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from core.database import get_db
from core.dependencies import get_current_user
from managers.formula_manager import FormulaManager
from managers.user_manager import UserManager
from models.user import User
from models.formula import UserFormula, FormulaType

router = APIRouter(prefix="/formulas", tags=["formulas"])

class FormulaCreate(BaseModel):
    formula_name: str = Field(..., min_length=1, max_length=100)
    formula: str = Field(..., min_length=1)
    sport: str = Field(..., min_length=2, max_length=10)
    formula_type: str = Field(default="ranking", pattern="^(ranking|metric|monte_carlo)$")
    description: Optional[str] = None

class FormulaResponse(BaseModel):
    id: int
    formula_name: str
    formula: str
    sport: str
    formula_type: str
    description: Optional[str]
    accuracy_score: int
    simulation_count: int
    created_at: str

@router.post("/", response_model=FormulaResponse, status_code=201)
async def create_formula(
    formula_data: FormulaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new formula"""
    user_manager = UserManager(db)
    if not user_manager.can_add_formula(current_user.id):
        limit = user_manager.get_user_tier_limit(current_user.id)
        raise HTTPException(
            status_code=400,
            detail=f"Formula limit reached. Your tier ({current_user.tier.value}) allows {limit} formulas."
        )
    
    formula_manager = FormulaManager(db)
    new_formula = formula_manager.create_formula(
        user_id=current_user.id,
        formula_name=formula_data.formula_name,
        formula=formula_data.formula,
        sport=formula_data.sport,
        formula_type=formula_data.formula_type,
        description=formula_data.description
    )
    
    return {
        'id': new_formula.id,
        'formula_name': new_formula.formula_name,
        'formula': new_formula.formula,
        'sport': new_formula.sport,
        'formula_type': new_formula.formula_type.value,
        'description': new_formula.description,
        'accuracy_score': new_formula.accuracy_score,
        'simulation_count': new_formula.simulation_count,
        'created_at': new_formula.created_at.isoformat()
    }

@router.get("/", response_model=List[FormulaResponse])
async def get_formulas(
    sport: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all formulas for current user"""
    formula_manager = FormulaManager(db)
    formulas = formula_manager.get_user_formulas(current_user.id)
    
    if sport:
        formulas = [f for f in formulas if f.sport == sport]
    
    return [{
        'id': f.id,
        'formula_name': f.formula_name,
        'formula': f.formula,
        'sport': f.sport,
        'formula_type': f.formula_type.value,
        'description': f.description,
        'accuracy_score': f.accuracy_score,
        'simulation_count': f.simulation_count,
        'created_at': f.created_at.isoformat()
    } for f in formulas]

@router.get("/{formula_id}", response_model=FormulaResponse)
async def get_formula(
    formula_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific formula"""
    formula_manager = FormulaManager(db)
    formula = formula_manager.get_formula_by_id(formula_id, current_user.id)
    if not formula:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    return {
        'id': formula.id,
        'formula_name': formula.formula_name,
        'formula': formula.formula,
        'sport': formula.sport,
        'formula_type': formula.formula_type.value,
        'description': formula.description,
        'accuracy_score': formula.accuracy_score,
        'simulation_count': formula.simulation_count,
        'created_at': formula.created_at.isoformat()
    }

@router.put("/{formula_id}", response_model=FormulaResponse)
async def update_formula(
    formula_id: int,
    formula_data: FormulaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a formula"""
    formula_manager = FormulaManager(db)
    updated = formula_manager.update_formula(
        formula_id=formula_id,
        user_id=current_user.id,
        formula_name=formula_data.formula_name,
        formula=formula_data.formula,
        description=formula_data.description
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    return {
        'id': updated.id,
        'formula_name': updated.formula_name,
        'formula': updated.formula,
        'sport': updated.sport,
        'formula_type': updated.formula_type.value,
        'description': updated.description,
        'accuracy_score': updated.accuracy_score,
        'simulation_count': updated.simulation_count,
        'created_at': updated.created_at.isoformat()
    }

@router.delete("/{formula_id}", status_code=204)
async def delete_formula(
    formula_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a formula"""
    formula_manager = FormulaManager(db)
    deleted = formula_manager.delete_formula(formula_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Formula not found")