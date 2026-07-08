# app.py - Simplified router mounting
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import Optional

from core.config import settings
from core.database import init_db, check_db_connection
from Sports import SportsManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize app
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

# Initialize database on startup
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

# ============ Import and Mount Routers ============
try:
    from routers.auth import router as auth_router
    from routers.users import router as users_router
    from routers.formulas import router as formulas_router
    from routers.gamelines import router as gamelines_router
    from routers.stats import router as stats_router
    
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(formulas_router)
    app.include_router(gamelines_router)
    app.include_router(stats_router)
    
    logger.info("✅ All routers mounted successfully")
except Exception as e:
    logger.error(f"❌ Error mounting routers: {e}")

# ============ Test Routes ============
@app.get("/ping")
async def ping():
    return {"message": "API is alive!"}

@app.get("/auth/ping-test")
async def auth_ping_test():
    return {"message": "Auth test is working"}

@app.get("/")
async def read_root():
    return {
        "message": "Winners Formula API is running!",
        "version": "2.0.0",
        "documentation": "/docs",
        "database": "PostgreSQL"
    }

@app.get("/health")
async def health_check():
    db_status = check_db_connection()
    return {
        "status": "healthy" if db_status else "degraded",
        "database": "connected" if db_status else "disconnected",
        "database_type": "PostgreSQL"
    }

# app.py - Add this at the bottom, before the if __name__ == "__main__" block

# ============ Direct Gamelines Endpoint ============
@app.get("/nfl/gamelines")
async def get_nfl_gamelines_direct(
    source: Optional[str] = Query(None, description="Sportsbook source"),
    force_refresh: bool = Query(False, description="Force refresh from API")
):
    """Get NFL gamelines directly"""
    from core.database import get_db as get_db_session
    from managers.gameline_manager import GamelineManager
    
    db = next(get_db_session())
    try:
        gameline_manager = GamelineManager(db)
        gamelines = gameline_manager.get_gamelines_by_sport("nfl", source)
        
        games = []
        for g in gamelines:
            games.append({
                'id': g.id,
                'sport': g.sport,
                'source': g.source,
                'game_id': g.game_id,
                'home_team_id': g.home_team_id,
                'away_team_id': g.away_team_id,
                'home_team': g.home_team if hasattr(g, 'home_team') else None,
                'away_team': g.away_team if hasattr(g, 'away_team') else None,
                'home_abbr': g.home_abbr if hasattr(g, 'home_abbr') else None,
                'away_abbr': g.away_abbr if hasattr(g, 'away_abbr') else None,
                'home_ml': g.home_ml,
                'away_ml': g.away_ml,
                'home_spread': g.home_spread,
                'away_spread': g.away_spread,
                'home_spread_odds': g.home_spread_odds,
                'away_spread_odds': g.away_spread_odds,
                'total': g.total,
                'over_odds': g.over_odds,
                'under_odds': g.under_odds,
                'game_day': g.game_date.strftime('%Y-%m-%d') if g.game_date else None,
                'start_time': g.start_time,
                'is_completed': g.is_completed,
                'home_score': g.home_score,
                'away_score': g.away_score,
            })
        
        return {
            'sport': 'nfl',
            'source': source or 'all',
            'games': games,
            'count': len(games)
        }
    except Exception as e:
        logger.error(f"Error getting NFL gamelines: {e}")
        return {
            'sport': 'nfl',
            'source': source or 'all',
            'games': [],
            'count': 0,
            'error': str(e)
        }
    finally:
        db.close()

# Generic endpoint for all sports
@app.get("/{sport}/gamelines")
async def get_sport_gamelines_direct(
    sport: str,
    source: Optional[str] = Query(None, description="Sportsbook source"),
    force_refresh: bool = Query(False, description="Force refresh from API")
):
    """Get gamelines for any sport directly"""
    from core.database import get_db as get_db_session
    from managers.gameline_manager import GamelineManager
    
    db = next(get_db_session())
    try:
        gameline_manager = GamelineManager(db)
        gamelines = gameline_manager.get_gamelines_by_sport(sport, source)
        
        games = []
        for g in gamelines:
            games.append({
                'id': g.id,
                'sport': g.sport,
                'source': g.source,
                'game_id': g.game_id,
                'home_team_id': g.home_team_id,
                'away_team_id': g.away_team_id,
                'home_ml': g.home_ml,
                'away_ml': g.away_ml,
                'home_spread': g.home_spread,
                'away_spread': g.away_spread,
                'home_spread_odds': g.home_spread_odds,
                'away_spread_odds': g.away_spread_odds,
                'total': g.total,
                'over_odds': g.over_odds,
                'under_odds': g.under_odds,
                'game_day': g.game_date.strftime('%Y-%m-%d') if g.game_date else None,
                'start_time': g.start_time,
                'is_completed': g.is_completed,
                'home_score': g.home_score,
                'away_score': g.away_score,
            })
        
        return {
            'sport': sport,
            'source': source or 'all',
            'games': games,
            'count': len(games)
        }
    except Exception as e:
        logger.error(f"Error getting {sport} gamelines: {e}")
        return {
            'sport': sport,
            'source': source or 'all',
            'games': [],
            'count': 0,
            'error': str(e)
        }
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )