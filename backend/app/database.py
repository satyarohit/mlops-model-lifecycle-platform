from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.models.domain import Base

# Configuration
SQLALCHEMY_DATABASE_URL = "postgresql://mlops:mlops_password@postgres:5432/mlops_db"
# For PostgreSQL: "postgresql://user:password@localhost/mlops"

# Engine configuration
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {},
    poolclass=StaticPool if "sqlite" in SQLALCHEMY_DATABASE_URL else None,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Dependency for getting DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


if "sqlite" in SQLALCHEMY_DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
