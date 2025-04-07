from sqlalchemy import create_engine
from .models import Base

# Database connection
DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:5432/aiconsole"
engine = create_engine(DATABASE_URL)

def init_db():
    """
    Initialize database tables
    """
    Base.metadata.create_all(engine)
    print("Database tables created successfully") 