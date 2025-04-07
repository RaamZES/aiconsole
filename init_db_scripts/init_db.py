from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# Create base class for models
Base = declarative_base()

class Chat(Base):
    __tablename__ = 'chats'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    last_modified = Column(DateTime, default=datetime.utcnow)
    chat_data = Column(Text, nullable=False)  # Store entire chat JSON as text

# Database connection
DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:5432/aiconsole"
engine = create_engine(DATABASE_URL)

# Create all tables
def init_db():
    Base.metadata.create_all(engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db() 