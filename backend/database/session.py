from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Default Postgres connection string
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:lightking@localhost:5432/pipeline_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
