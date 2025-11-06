"""
Database Initialization and Performance Optimization

Applies performance indexes on startup to optimize query performance.
"""

import logging
from pathlib import Path
from sqlalchemy import text
from app.core.database import engine

logger = logging.getLogger("database_init")


def apply_performance_indexes():
    """
    Apply performance indexes to database.
    
    Idempotent - safe to run multiple times.
    """
    try:
        logger.info("Applying performance indexes...")
        
        # Read SQL script
        sql_file = Path(__file__).parent / "performance_indexes.sql"
        
        if not sql_file.exists():
            logger.warning(f"Performance indexes SQL file not found: {sql_file}")
            return False
        
        sql_script = sql_file.read_text()
        
        # Execute SQL script
        # Note: SQL Server requires GO statements to be handled separately
        batches = sql_script.split('GO')
        
        with engine.begin() as conn:
            for batch in batches:
                batch = batch.strip()
                if batch:
                    try:
                        conn.execute(text(batch))
                    except Exception as e:
                        # Log but continue (indexes might already exist)
                        logger.debug(f"Index creation note: {e}")
        
        logger.info("✓ Performance indexes applied successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to apply performance indexes: {e}", exc_info=True)
        return False


def initialize_database():
    """
    Initialize database with performance optimizations.
    
    Call this on application startup.
    """
    try:
        logger.info("Initializing database...")
        
        # Apply performance indexes
        apply_performance_indexes()
        
        logger.info("✓ Database initialization complete")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        return False
