from sqlalchemy import Column, String, Text, DateTime
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