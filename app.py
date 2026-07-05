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

# Add CORS middleware
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
    logger.info("Initializing database...")
    init_db()
    
    if check_db_connection():
        logger.info("Database connection successful")
    else:
        logger.error("Database connection failed")
    
    def cleanup_loop():
        while True:
            try:
                cleanup_gamelines()
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
            time.sleep(3600)
    
    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()
    logger.info("Background cleanup thread started")

# Import routers
from routers import auth, users, formulas, gamelines, stats

# Include all routers
app.include_router(auth.router)      # /auth/login, /auth/register
app.include_router(users.router)      # /users/me, /users/me/password
app.include_router(formulas.router)   # /formulas
app.include_router(gamelines.router)  # /gamelines
app.include_router(stats.router)      # /stats

# Direct endpoints (for backward compatibility)
@app.get("/{sport}/gamelines")
async def get_gamelines_direct(
    sport: str,
    source: Optional[str] = Query(None),
    force_refresh: bool = Query(False)
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
        'count': len(SportsManager.SUPPORTED_SPORTS)
    }

@app.post("/admin/cleanup")
async def trigger_cleanup(background_tasks: BackgroundTasks):
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
        "supported_sports": SportsManager.SUPPORTED_SPORTS
    }

@app.get("/health")
async def health_check():
    db_status = check_db_connection()
    return {
        "status": "healthy" if db_status else "degraded",
        "database": "connected" if db_status else "disconnected",
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