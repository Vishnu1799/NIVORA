from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

db_url = settings.database_url

# Fallback to SQLite if PostgreSQL connection fails or if sqlite is configured
try:
    if "postgresql" in db_url:
        # Check if connect_args needed
        engine = create_engine(db_url, pool_pre_ping=True)
    else:
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
except Exception as e:
    logger.warning(f"Database connection error with {db_url}: {e}. Falling back to SQLite.")
    engine = create_engine("sqlite:///./nivora.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
