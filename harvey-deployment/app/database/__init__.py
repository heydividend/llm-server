"""
Database package for Harvey

Contains database initialization and performance optimization scripts.
"""

from app.database.init_db import initialize_database, apply_performance_indexes

__all__ = ["initialize_database", "apply_performance_indexes"]
