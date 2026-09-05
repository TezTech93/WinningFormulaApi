from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.database import get_db
from core.dependencies import get_current_user
from Sports.nfl.nfl_coaches import nfl_coaches

router = APIRouter(prefix="/coaches", tags=["coaches"])

@router.get("/nfl")
async def get_nfl_coaches():
    return nfl_coaches

# Generic endpoint for future expansion
@router.get("/{sport}")
async def get_coaches(sport: str):
    if sport == "nfl":
        return nfl_coaches
    # Add other sports later
    return []