# routers/predictions.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from core.database import get_db
from core.dependencies import get_current_user,require_subscription
from models.user import User
from models.predictions import UserPrediction, PredictionType

router = APIRouter(prefix="/predictions", tags=["Predictions"])


# ---------- Pydantic schemas ----------
class PredictionCreate(BaseModel):
    game_id: str
    sport: str
    home_team: str
    away_team: str
    home_abbr: str
    away_abbr: str
    prediction_type: str = Field(..., pattern="^(home|away|over|under|spread_home|spread_away)$")
    predicted_value: Optional[float] = None
    formula_id: Optional[int] = None
    confidence: Optional[float] = None


class ResultUpdate(BaseModel):
    home_score: int
    away_score: int


class PredictionResponse(BaseModel):
    id: int
    game_id: str
    sport: str
    home_team: str
    away_team: str
    home_abbr: str
    away_abbr: str
    prediction_type: str
    predicted_value: Optional[float]
    home_score: Optional[int]
    away_score: Optional[int]
    is_correct: Optional[bool]
    status: str
    created_at: str


def _to_response(p: UserPrediction) -> dict:
    return {
        "id": p.id,
        "game_id": p.game_id,
        "sport": p.sport,
        "home_team": p.home_team,
        "away_team": p.away_team,
        "home_abbr": p.home_abbr,
        "away_abbr": p.away_abbr,
        "prediction_type": p.prediction_type.value if hasattr(p.prediction_type, "value") else p.prediction_type,
        "predicted_value": p.predicted_value,
        "home_score": p.home_score,
        "away_score": p.away_score,
        "is_correct": p.is_correct,
        "status": p.status,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


# ---------- Endpoints ----------
@router.post("/", response_model=PredictionResponse, status_code=201)
async def create_prediction(
    data: PredictionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_tier: User = Depends(require_subscription)
):
    pred = UserPrediction(
        user_id=current_user.id,
        game_id=data.game_id,
        sport=data.sport,
        home_team=data.home_team,
        away_team=data.away_team,
        home_abbr=data.home_abbr,
        away_abbr=data.away_abbr,
        prediction_type=PredictionType(data.prediction_type),
        predicted_value=data.predicted_value,
        status="upcoming",
    )
    db.add(pred)
    db.commit()
    db.refresh(pred)
    return _to_response(pred)


@router.get("/", response_model=List[PredictionResponse])
async def list_predictions(
    sport: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_tier: User = Depends(require_subscription)
):
    q = db.query(UserPrediction).filter(UserPrediction.user_id == current_user.id)
    if sport:
        q = q.filter(UserPrediction.sport == sport)
    if status:
        q = q.filter(UserPrediction.status == status)
    preds = q.order_by(UserPrediction.created_at.desc()).all()
    return [_to_response(p) for p in preds]


@router.put("/{prediction_id}/result", response_model=PredictionResponse)
async def update_result(
    prediction_id: int,
    data: ResultUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_tier: User = Depends(require_subscription)
):
    pred = (
        db.query(UserPrediction)
        .filter(UserPrediction.id == prediction_id, UserPrediction.user_id == current_user.id)
        .first()
    )
    if not pred:
        raise HTTPException(404, "Prediction not found")

    pred.home_score = data.home_score
    pred.away_score = data.away_score
    pred.status = "final"

    # Determine if correct based on prediction type
    ptype = pred.prediction_type.value if hasattr(pred.prediction_type, "value") else pred.prediction_type
    home_won = data.home_score > data.away_score

    if ptype == "home":
        pred.is_correct = home_won
    elif ptype == "away":
        pred.is_correct = not home_won
    elif ptype == "over":
        pred.is_correct = (data.home_score + data.away_score) > (pred.predicted_value or 0)
    elif ptype == "under":
        pred.is_correct = (data.home_score + data.away_score) < (pred.predicted_value or 0)
    elif ptype == "spread_home":
        margin = data.home_score - data.away_score
        pred.is_correct = margin > (pred.predicted_value or 0)
    elif ptype == "spread_away":
        margin = data.home_score - data.away_score
        pred.is_correct = margin < (pred.predicted_value or 0)

    db.commit()
    db.refresh(pred)
    return _to_response(pred)


@router.get("/analytics")
async def get_analytics(
    sport: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_tier: User = Depends(require_subscription)
):
    """Aggregate accuracy stats per sport and per formula."""
    q = db.query(UserPrediction).filter(
        UserPrediction.user_id == current_user.id,
        UserPrediction.is_correct.isnot(None),
    )
    if sport:
        q = q.filter(UserPrediction.sport == sport)
    preds = q.all()

    total = len(preds)
    correct = sum(1 for p in preds if p.is_correct)
    by_sport = {}
    for p in preds:
        s = by_sport.setdefault(p.sport, {"total": 0, "correct": 0})
        s["total"] += 1
        if p.is_correct:
            s["correct"] += 1

    return {
        "total": total,
        "correct": correct,
        "accuracy": round(correct / total * 100, 2) if total else 0,
        "by_sport": {
            s: {**v, "accuracy": round(v["correct"] / v["total"] * 100, 2) if v["total"] else 0}
            for s, v in by_sport.items()
        },
        "predictions": [_to_response(p) for p in preds],
    }


@router.delete("/{prediction_id}", status_code=204)
async def delete_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_tier: User = Depends(require_subscription)
):
    pred = (
        db.query(UserPrediction)
        .filter(UserPrediction.id == prediction_id, UserPrediction.user_id == current_user.id)
        .first()
    )
    if not pred:
        raise HTTPException(404, "Prediction not found")
    db.delete(pred)
    db.commit()
    return None

from services.simulation_service import SimulationService

class SimulationRequest(BaseModel):
    formula_id: int
    game_ids: List[str]
    sport: str
    randomness: float = 0.2
    iterations: int = 1000

@router.post("/simulate")
async def simulate(
    req: SimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_tier: User = Depends(require_subscription)
):
    svc = SimulationService(db)
    results = svc.run(
        formula_id=req.formula_id,
        game_ids=req.game_ids,
        sport=req.sport,
        randomness=req.randomness,
        iterations=req.iterations,
    )
    return {"results": results}