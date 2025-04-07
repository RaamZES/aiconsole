from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
import logging
from ..db.models import Base, Chat

# Database connection
DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:5432/aiconsole"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

_log = logging.getLogger(__name__)

def get_session():
    session = SessionLocal()
    try:
        return session
    except Exception as e:
        session.close()
        raise e

def save_chat_to_db(chat_data):
    """
    Save chat to database as JSON text
    
    Args:
        chat_data (dict): Chat data in JSON format
        
    Returns:
        str: ID of the saved chat
    """
    session = get_session()
    try:
        # Convert chat data to JSON string
        try:
            chat_json = json.dumps(chat_data, ensure_ascii=False, default=str)
        except Exception as e:
            _log.error(f"Error serializing chat data to JSON: {e}")
            _log.error(f"Chat data: {chat_data}")
            raise e
        
        # Check if chat exists
        existing_chat = session.query(Chat).filter(Chat.id == chat_data["id"]).first()
        
        if existing_chat:
            # Update existing chat
            existing_chat.name = chat_data["name"]
            existing_chat.last_modified = datetime.utcnow()
            existing_chat.chat_data = chat_json
            _log.debug(f"Updated chat {chat_data['id']} in database")
        else:
            # Create new chat
            chat = Chat(
                id=chat_data["id"],
                name=chat_data["name"],
                last_modified=datetime.utcnow(),
                chat_data=chat_json
            )
            session.add(chat)
            _log.debug(f"Created new chat {chat_data['id']} in database")
        
        session.commit()
        return chat_data["id"]
    
    except Exception as e:
        session.rollback()
        _log.error(f"Error saving chat to database: {e}")
        raise e
    finally:
        session.close()

def load_chat_from_db(chat_id):
    """
    Load chat from database
    
    Args:
        chat_id (str): Chat ID
        
    Returns:
        dict: Chat data in JSON format
    """
    session = get_session()
    try:
        # Get chat
        chat = session.query(Chat).filter(Chat.id == chat_id).first()
        
        if not chat:
            return None
        
        # Convert JSON string back to dictionary
        return json.loads(chat.chat_data)
    
    except Exception as e:
        raise e
    finally:
        session.close()

def list_chats():
    """
    Get list of all chats
    
    Returns:
        list: List of chats with basic information
    """
    session = get_session()
    try:
        chats = session.query(Chat).all()
        
        result = []
        for chat in chats:
            result.append({
                "id": chat.id,
                "name": chat.name,
                "last_modified": chat.last_modified
            })
        
        return result
    
    except Exception as e:
        raise e
    finally:
        session.close()

def delete_chat(chat_id):
    """
    Delete chat from database
    
    Args:
        chat_id (str): Chat ID
    """
    session = get_session()
    try:
        chat = session.query(Chat).filter(Chat.id == chat_id).first()
        if chat:
            session.delete(chat)
            session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close() 