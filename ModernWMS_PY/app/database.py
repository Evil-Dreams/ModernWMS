from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, Session

from .config import DATABASE_URL

# Configure SQLAlchemy to use connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_size=5,
    max_overflow=10,
    echo=False  # Set to True for SQL query logging
)

# Create a scoped session factory
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SessionLocal = scoped_session(session_factory)

# Base class for all models
Base = declarative_base()

# Set a default schema if needed
# Base.metadata.schema = 'public'

@contextmanager
def get_db() -> Session:
    """Dependency for getting a database session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()

# Enable foreign key support for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in str(dbapi_connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

def init_db():
    """
    Initialize the database by creating all tables.
    Call this once when the application starts.
    """
    Base.metadata.create_all(bind=engine)

def clear_data():
    """
    Clear all data from all tables (for testing).
    Be very careful with this in production!
    """
    db = SessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()
