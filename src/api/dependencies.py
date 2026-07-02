"""
Shared FastAPI dependencies.
Provides PostgreSQL DB session to all route handlers.
"""

from src.database.connection import get_db, init_db

# Re-export get_db so routes import from one place
__all__ = ["get_db", "init_db"]