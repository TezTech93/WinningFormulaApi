# core/database.py
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, List, Dict
import logging
import os

from core.config import settings

logger = logging.getLogger(__name__)

# Get database URL from settings
DATABASE_URL = settings.DATABASE_URL

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
        logger.info("PostgreSQL database tables created successfully")
        
        # Print table schema for debugging
        print_table_schema()
        
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

def get_table_columns(table_name: str) -> List[Dict[str, str]]:
    """Get all columns for a specific table"""
    try:
        db = SessionLocal()
        result = db.execute(text(f"""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """))
        
        columns = []
        for row in result:
            columns.append({
                'name': row[0],
                'type': row[1],
                'nullable': row[2],
                'default': row[3]
            })
        
        db.close()
        return columns
    except Exception as e:
        logger.error(f"Error getting columns for {table_name}: {e}")
        return []

def print_table_schema():
    """Print all table schemas for debugging"""
    try:
        db = SessionLocal()
        
        # Get all tables
        result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        
        tables = [row[0] for row in result]
        
        logger.info("=" * 80)
        logger.info("📊 DATABASE SCHEMA OVERVIEW")
        logger.info("=" * 80)
        
        for table in tables:
            columns = get_table_columns(table)
            
            logger.info(f"\n📋 Table: {table}")
            logger.info("-" * 40)
            logger.info(f"{'Column':<25} {'Type':<20} {'Nullable':<10} {'Default':<15}")
            logger.info("-" * 70)
            
            for col in columns:
                logger.info(
                    f"{col['name']:<25} "
                    f"{col['type']:<20} "
                    f"{col['nullable']:<10} "
                    f"{col['default'] or 'NULL':<15}"
                )
            
            logger.info(f"Total columns: {len(columns)}")
        
        logger.info("\n" + "=" * 80)
        db.close()
        
    except Exception as e:
        logger.error(f"Error printing schema: {e}")

def get_table_schema_json(table_name: str) -> Dict:
    """Get table schema as JSON for API responses"""
    columns = get_table_columns(table_name)
    return {
        'table_name': table_name,
        'columns': columns,
        'column_names': [col['name'] for col in columns],
        'count': len(columns)
    }

def get_all_schemas_json() -> Dict:
    """Get all schemas as JSON"""
    try:
        db = SessionLocal()
        result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        
        tables = [row[0] for row in result]
        db.close()
        
        schemas = {}
        for table in tables:
            schemas[table] = get_table_schema_json(table)
        
        return schemas
    except Exception as e:
        logger.error(f"Error getting schemas: {e}")
        return {}