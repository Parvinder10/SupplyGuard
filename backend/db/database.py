import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.core.config import settings

logger = logging.getLogger("Database")

# Check if PostgreSQL is accessible
engine = None
SessionLocal = None

try:
    engine = create_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        connect_args={"connect_timeout": 3}
    )
    # Test connection
    with engine.connect() as conn:
        logger.info("Connected successfully to PostgreSQL warehouse.")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.warning(f"PostgreSQL not immediately reachable at {settings.SQLALCHEMY_DATABASE_URI}: {e}. Initializing local SQLite fallback for testing/dev.")
    FALLBACK_DB = "sqlite:///./supplyguard_dev.db"
    engine = create_engine(FALLBACK_DB, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
