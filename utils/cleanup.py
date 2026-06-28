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
        manager = GamelineManager(db)
        
        # Mark completed games
        marked = manager.mark_completed_games()
        
        # Delete old completed games (older than 7 days)
        deleted = manager.delete_old_gamelines(days=7)
        
        logger.info(f"Cleanup completed: marked {marked} games as completed, deleted {deleted} old games")
        
        return {
            'marked_completed': marked,
            'deleted_old': deleted,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
        return None
    finally:
        db.close()

def run_cleanup_scheduled():
    """Run cleanup as a scheduled task"""
    # This can be called from a scheduler or cron job
    return cleanup_gamelines()

if __name__ == "__main__":
    # Run directly for testing
    result = run_cleanup_scheduled()
    print(result)