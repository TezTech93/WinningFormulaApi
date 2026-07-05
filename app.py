# app.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import Optional
import threading
import time

from core.config import settings
from core.database import init_db, check_db_connection
from Sports.manager import SportsManager
from utils.cleanup import cleanup_gamelines

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

# ============ CORS Middleware ============
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8081",
        "http://localhost:19006",
        "http://localhost:3000",
        "https://winningformulaapi.onrender.com",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ============ Database Initialization ============
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
    
    # Start background cleanup thread
    def cleanup_loop():
        while True:
            try:
                cleanup_gamelines()
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
            time.sleep(3600)  # Run every hour
    
    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()
    logger.info("Background cleanup thread started")

# ============ Import Routers ============
from routers import auth, users, formulas, gamelines, stats, parlays, strategies

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(formulas.router, prefix="/formulas", tags=["Formulas"])
app.include_router(gamelines.router, prefix="/gamelines", tags=["Gamelines"])
app.include_router(stats.router, prefix="/stats", tags=["Stats"])
app.include_router(parlays.router, prefix="/parlays", tags=["Parlays"])
app.include_router(strategies.router, prefix="/strategies", tags=["Strategies"])

# ============ Direct Endpoints for Backward Compatibility ============
@app.get("/{sport}/gamelines")
async def get_gamelines_direct(
    sport: str,
    source: Optional[str] = Query(None, description="Sportsbook source"),
    force_refresh: bool = Query(False, description="Force refresh from API")
):
    """Get gamelines for a specific sport"""
    if sport not in SportsManager.SUPPORTED_SPORTS:
        raise HTTPException(status_code=400, detail=f"Unsupported sport: {sport}")
    
    result = await SportsManager.get_gamelines(sport, source, force_refresh)
    
    if result.get('error'):
        raise HTTPException(status_code=404, detail=result['error'])
    
    return result

@app.get("/{sport}/stats/{team}/{year}")
async def get_team_stats_direct(
    sport: str,
    team: str,
    year: str
):
    """Get team stats for a specific sport"""
    if sport not in SportsManager.SUPPORTED_SPORTS:
        raise HTTPException(status_code=400, detail=f"Unsupported sport: {sport}")
    
    result = await SportsManager.get_team_stats(sport, team, year)
    
    if result.get('error'):
        raise HTTPException(status_code=404, detail=result['error'])
    
    return result

@app.get("/sports")
async def get_supported_sports():
    """Get list of supported sports"""
    return {
        'sports': SportsManager.SUPPORTED_SPORTS,
        'count': len(SportsManager.SUPPORTED_SPORTS),
        'info': {sport: SportsManager.get_sport_info(sport) for sport in SportsManager.SUPPORTED_SPORTS}
    }

@app.post("/admin/cleanup")
async def trigger_cleanup(background_tasks: BackgroundTasks):
    """Trigger manual cleanup of gamelines"""
    background_tasks.add_task(cleanup_gamelines)
    return {
        'message': 'Cleanup triggered',
        'status': 'running in background'
    }

@app.get("/")
async def read_root():
    return {
        "message": "Winners Formula API is running!",
        "version": "2.0.0",
        "documentation": "/docs",
        "database": "PostgreSQL",
        "supported_sports": SportsManager.SUPPORTED_SPORTS
    }

@app.get("/health")
async def health_check():
    db_status = check_db_connection()
    return {
        "status": "healthy" if db_status else "degraded",
        "database": "connected" if db_status else "disconnected",
        "database_type": "PostgreSQL",
        "sports": SportsManager.SUPPORTED_SPORTS
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )