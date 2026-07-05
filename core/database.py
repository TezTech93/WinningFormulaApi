# core/database.py
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging
import os

from core.config import settings

logger = logging.getLogger(__name__)

# Get database URL from settings or environment
DATABASE_URL = os.getenv("DATABASE_URL", settings.DATABASE_URL)

# Create engine with PostgreSQL
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    try:
        # Import all models to ensure they're registered
        import models
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully in PostgreSQL")
        
        # Check if users table has data
        db = SessionLocal()
        try:
            from models.user import User
            user_count = db.query(User).count()
            logger.info(f"Users in database: {user_count}")
        except Exception as e:
            logger.warning(f"Could not check users: {e}")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

def check_db_connection():
    """Check if database connection is working"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("PostgreSQL connection successful")
        return True
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        return False