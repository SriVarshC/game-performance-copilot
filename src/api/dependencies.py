"""
Shared FastAPI dependencies.
Provides PostgreSQL DB session + JWT auth to all route handlers.
"""

from src.database.connection import get_db, init_db
from src.auth.security import get_current_user

# Re-export so routes import from one place
__all__ = ["get_db", "init_db", "get_current_user"]