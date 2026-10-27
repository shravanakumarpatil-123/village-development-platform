"""
Opens the connection to PostgreSQL and hands out a fresh "session" (a working
connection) to every API request that needs to touch the database.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Used by FastAPI as a dependency: opens a DB session for one request,
    and always closes it afterwards, even if the request raises an error.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
