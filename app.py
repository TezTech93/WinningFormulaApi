# app.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Query, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging
from typing import Optional, List, Dict, Any

from Sports.manager import sports_manager
from core.database import get_db, init_db, check_db_connection

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Winners Formula API",
    description="Sports betting analytics and formula management API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing PostgreSQL database...")
    try:
        init_db()
        logger.info("Database initialized successfully")
        if check_db_connection():
            logger.info("PostgreSQL connection successful")
        else:
            logger.error("PostgreSQL connection failed")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

# Import routers
from routers import auth, users, formulas, stats

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(formulas.router)
app.include_router(stats.router)

# ============ Pydantic Models for Manual Input ============
class GamelineInput(BaseModel):
    game_id: Optional[str] = None
    game_day: str
    start_time: Optional[str] = None
    home_team: str
    away_team: str
    home_abbr: Optional[str] = None
    away_abbr: Optional[str] = None
    home_ml: Optional[int] = None
    away_ml: Optional[int] = None
    home_spread: Optional[float] = None
    away_spread: Optional[float] = None
    home_spread_odds: Optional[int] = None
    away_spread_odds: Optional[int] = None
    over_under: Optional[float] = None
    over_odds: Optional[int] = None
    under_odds: Optional[int] = None
    is_completed: Optional[bool] = False

# ============ Gamelines Endpoints ============
@app.get("/{sport}/gamelines")
async def get_sport_gamelines(
    sport: str,
    force_refresh: bool = Query(False, description="Force refresh from web"),
    db: Session = Depends(get_db)
):
    """Get gamelines for a specific sport"""
    if sport not in sports_manager.SUPPORTED_SPORTS:
        raise HTTPException(status_code=400, detail=f"Unsupported sport: {sport}")
    
    result = await sports_manager.get_gamelines(sport, db, force_refresh)
    
    if result.get('error'):
        raise HTTPException(status_code=404, detail=result['error'])
    
    return result

@app.get("/{sport}/season-phase")
async def get_season_phase(
    sport: str,
    db: Session = Depends(get_db)
):
    """Get current season phase for a sport"""
    if sport not in sports_manager.SUPPORTED_SPORTS:
        raise HTTPException(status_code=400, detail=f"Unsupported sport: {sport}")
    
    result = await sports_manager.get_season_phase(sport, db)
    
    if result.get('error'):
        raise HTTPException(status_code=404, detail=result['error'])
    
    return result

# ============ Manual Gameline Input Endpoints ============
@app.post("/{sport}/gamelines/manual")
async def add_manual_gameline(
    sport: str,
    game_data: GamelineInput,
    db: Session = Depends(get_db)
):
    """Add a single gameline manually"""
    if sport not in sports_manager.SUPPORTED_SPORTS:
        raise HTTPException(status_code=400, detail=f"Unsupported sport: {sport}")
    
    result = sports_manager.manual_add_gameline(sport, db, game_data.dict())
    
    if result.get('error'):
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result

@app.post("/{sport}/gamelines/manual/bulk")
async def add_manual_gamelines_bulk(
    sport: str,
    games_data: List[GamelineInput] = Body(...),
    db: Session = Depends(get_db)
):
    """Add multiple gamelines manually from JSON data"""
    if sport not in sports_manager.SUPPORTED_SPORTS:
        raise HTTPException(status_code=400, detail=f"Unsupported sport: {sport}")
    
    if not games_data:
        raise HTTPException(status_code=400, detail="No games provided")
    
    # Convert to dict list
    games_dict = [game.dict() for game in games_data]
    
    result = sports_manager.manual_add_gamelines_bulk(sport, db, games_dict)
    
    if result.get('error'):
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result

# ============ Sports Endpoints ============
@app.get("/sports")
async def get_supported_sports():
    return {
        'sports': sports_manager.SUPPORTED_SPORTS,
        'count': len(sports_manager.SUPPORTED_SPORTS)
    }

@app.get("/")
async def read_root():
    return {
        "message": "Winners Formula API is running!",
        "version": "2.0.0",
        "documentation": "/docs",
        "supported_sports": sports_manager.SUPPORTED_SPORTS,
        "database": "PostgreSQL"
    }

@app.get("/health")
async def health_check():
    db_status = check_db_connection()
    return {
        "status": "healthy" if db_status else "degraded",
        "database": "connected" if db_status else "disconnected",
        "database_type": "PostgreSQL",
        "supported_sports": sports_manager.SUPPORTED_SPORTS
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )