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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )