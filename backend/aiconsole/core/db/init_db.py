from sqlalchemy import create_engine
from .models import Base
from .chat_db_operations import engine

def init_db():
    """
    Initialize database tables
    """
    # Drop all existing tables
    Base.metadata.drop_all(engine)
    
    # Create all tables
    Base.metadata.create_all(engine)
    print("Database tables created successfully")

if __name__ == "__main__":
    init_db() 