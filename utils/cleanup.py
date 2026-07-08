# utils/cleanup.py
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
from managers.gameline_manager import GamelineManager
from core.database import SessionLocal

logger = logging.getLogger(__name__)

def cleanup_gamelines():
    """Background task to clean up old gamelines"""
    db = SessionLocal()
    try:
        # Use raw SQL to avoid model issues
        from sqlalchemy import text
        now = datetime.now()
        
        # Mark completed games
        db.execute(
            text("UPDATE gamelines SET is_completed = true WHERE is_completed = false AND game_date < :now"),
            {"now": now}
        )
        db.commit()
        
        # Delete old completed games
        cutoff = now - timedelta(days=7)
        db.execute(
            text("DELETE FROM gamelines WHERE is_completed = true AND game_date < :cutoff"),
            {"cutoff": cutoff}
        )
        db.commit()
        
        logger.info("Cleanup completed successfully")
        
        return {
            'marked_completed': True,
            'deleted_old': True,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
        db.rollback()
        return None
    finally:
        db.close()