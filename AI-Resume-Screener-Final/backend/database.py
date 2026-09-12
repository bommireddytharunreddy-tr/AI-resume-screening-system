from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'resume.db'}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def migrate_existing_database() -> None:
    """Add new recruiter fields without destroying an existing local database."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if "resumes" not in tables:
        return

    existing = {column["name"] for column in inspector.get_columns("resumes")}
    additions = {
        "candidate_name": "TEXT",
        "email": "TEXT",
        "phone": "TEXT",
        "job_title": "TEXT",
        "status": "TEXT DEFAULT 'Review'",
        "recruiter_notes": "TEXT",
        "created_at": "DATETIME",
    }

    with engine.begin() as connection:
        for column, definition in additions.items():
            if column not in existing:
                connection.execute(
                    text(f"ALTER TABLE resumes ADD COLUMN {column} {definition}")
                )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
