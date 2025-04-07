#!/usr/bin/env python
"""
Script to demonstrate replacing JSON file operations with PostgreSQL database operations
for saving and reading chats.
"""

import os
import sys
import json
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from init_db import Base, Chat, MessageGroup, Message, ToolCall

# Create base class for models
Base = declarative_base()

# Define models
class Chat(Base):
    __tablename__ = 'chats'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    title_edited = Column(Boolean, default=False)
    last_modified = Column(DateTime, default=datetime.utcnow)
    agent_id = Column(String, nullable=False)
    is_analysis_in_progress = Column(Boolean, default=False)
    chat_options = Column(JSON)
    chat_data = Column(Text)
    
    # Relationships
    message_groups = relationship("MessageGroup", back_populates="chat", cascade="all, delete-orphan")

class MessageGroup(Base):
    __tablename__ = 'message_groups'
    
    id = Column(String, primary_key=True)
    chat_id = Column(String, ForeignKey('chats.id'), nullable=False)
    actor_type = Column(String, nullable=False)
    actor_id = Column(String, nullable=False)
    role = Column(String, nullable=False)
    task = Column(String)
    analysis = Column(Text)
    materials_ids = Column(JSON)
    
    # Relationships
    chat = relationship("Chat", back_populates="message_groups")
    messages = relationship("Message", back_populates="group", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(String, primary_key=True)
    group_id = Column(String, ForeignKey('message_groups.id'), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_streaming = Column(Boolean, default=False)
    requested_format = Column(String)
    
    # Relationships
    group = relationship("MessageGroup", back_populates="messages")
    tool_calls = relationship("ToolCall", back_populates="message", cascade="all, delete-orphan")

class ToolCall(Base):
    __tablename__ = 'tool_calls'
    
    id = Column(String, primary_key=True)
    message_id = Column(String, ForeignKey('messages.id'), nullable=False)
    name = Column(String, nullable=False)
    arguments = Column(JSON)
    
    # Relationships
    message = relationship("Message", back_populates="tool_calls")

# Database connection parameters
DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:5432/aiconsole"

# Create engine
engine = create_engine(DATABASE_URL)

# Create all tables if they don't exist
Base.metadata.create_all(engine)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    """Get database session"""
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
        chat_json = json.dumps(chat_data, ensure_ascii=False)
        
        # Check if chat exists
        existing_chat = session.query(Chat).filter(Chat.id == chat_data["id"]).first()
        
        if existing_chat:
            # Update existing chat
            existing_chat.name = chat_data["name"]
            existing_chat.title_edited = chat_data.get("title_edited", False)
            existing_chat.last_modified = datetime.utcnow()
            existing_chat.agent_id = chat_data["agent_id"]
            existing_chat.is_analysis_in_progress = chat_data.get("is_analysis_in_progress", False)
            existing_chat.chat_options = chat_data.get("chat_options", {})
            existing_chat.chat_data = chat_json
            
            # Удаляем существующие группы сообщений
            for group in existing_chat.message_groups:
                session.delete(group)
            
            chat = existing_chat
        else:
            # Создаем новый чат
            chat = Chat(
                id=chat_data["id"],
                name=chat_data["name"],
                title_edited=chat_data.get("title_edited", False),
                last_modified=datetime.utcnow(),
                agent_id=chat_data["agent_id"],
                is_analysis_in_progress=chat_data.get("is_analysis_in_progress", False),
                chat_options=chat_data.get("chat_options", {}),
                chat_data=chat_json
            )
            session.add(chat)
        
        # Добавляем группы сообщений
        for group_data in chat_data.get("message_groups", []):
            group = MessageGroup(
                id=group_data["id"],
                chat_id=chat.id,
                actor_type=group_data["actor_type"],
                actor_id=group_data["actor_id"],
                role=group_data["role"],
                task=group_data.get("task"),
                analysis=group_data.get("analysis"),
                materials_ids=group_data.get("materials_ids", [])
            )
            session.add(group)
            
            # Добавляем сообщения
            for message_data in group_data.get("messages", []):
                message = Message(
                    id=message_data["id"],
                    group_id=group.id,
                    content=message_data["content"],
                    timestamp=datetime.fromisoformat(message_data["timestamp"]) if isinstance(message_data["timestamp"], str) else message_data["timestamp"],
                    requested_format=message_data.get("requested_format"),
                    is_streaming=message_data.get("is_streaming", False)
                )
                session.add(message)
                
                # Добавляем вызовы инструментов
                for tool_call_data in message_data.get("tool_calls", []):
                    tool_call = ToolCall(
                        id=tool_call_data["id"],
                        message_id=message.id,
                        name=tool_call_data["name"],
                        arguments=tool_call_data.get("arguments", {})
                    )
                    session.add(tool_call)
        
        session.commit()
        return chat.id
    
    except Exception as e:
        session.rollback()
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

def create_new_chat(name, agent_id):
    """
    Создание нового чата
    
    Args:
        name (str): Название чата
        agent_id (str): ID агента
        
    Returns:
        str: ID созданного чата
    """
    session = get_session()
    try:
        chat_id = str(uuid.uuid4())
        
        chat = Chat(
            id=chat_id,
            name=name,
            title_edited=False,
            last_modified=datetime.utcnow(),
            agent_id=agent_id,
            is_analysis_in_progress=False,
            chat_options={}
        )
        
        session.add(chat)
        session.commit()
        
        return chat_id
    
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def add_message_to_chat(chat_id, actor_type, actor_id, role, content, task=None, analysis=None, materials_ids=None):
    """
    Добавление сообщения в чат
    
    Args:
        chat_id (str): ID чата
        actor_type (str): Тип отправителя ("user" или "agent")
        actor_id (str): ID отправителя
        role (str): Роль отправителя ("user" или "assistant")
        content (str): Текст сообщения
        task (str, optional): Задача
        analysis (str, optional): Анализ
        materials_ids (list, optional): ID materials
        
    Returns:
        tuple: (ID группы сообщений, ID сообщения)
    """
    session = get_session()
    try:
        # Получаем чат
        chat = session.query(Chat).filter(Chat.id == chat_id).first()
        
        if not chat:
            raise ValueError(f"Чат с ID {chat_id} не найден")
        
        # Создаем группу сообщений
        group_id = str(uuid.uuid4())
        group = MessageGroup(
            id=group_id,
            chat_id=chat_id,
            actor_type=actor_type,
            actor_id=actor_id,
            role=role,
            task=task,
            analysis=analysis,
            materials_ids=materials_ids or []
        )
        
        session.add(group)
        
        # Создаем сообщение
        message_id = str(uuid.uuid4())
        message = Message(
            id=message_id,
            group_id=group_id,
            content=content,
            timestamp=datetime.utcnow(),
            is_streaming=False
        )
        
        session.add(message)
        
        # Обновляем время последнего изменения чата
        chat.last_modified = datetime.utcnow()
        
        session.commit()
        
        return group_id, message_id
    
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def add_tool_call_to_message(message_id, name, arguments):
    """
    Добавление вызова инструмента к сообщению
    
    Args:
        message_id (str): ID сообщения
        name (str): Название инструмента
        arguments (dict): Аргументы вызова
        
    Returns:
        str: ID вызова инструмента
    """
    session = get_session()
    try:
        # Получаем сообщение
        message = session.query(Message).filter(Message.id == message_id).first()
        
        if not message:
            raise ValueError(f"Сообщение с ID {message_id} не найдено")
        
        # Создаем вызов инструмента
        tool_call_id = str(uuid.uuid4())
        tool_call = ToolCall(
            id=tool_call_id,
            message_id=message_id,
            name=name,
            arguments=arguments
        )
        
        session.add(tool_call)
        
        # Обновляем время последнего изменения чата
        group = session.query(MessageGroup).filter(MessageGroup.id == message.group_id).first()
        if group:
            chat = session.query(Chat).filter(Chat.id == group.chat_id).first()
            if chat:
                chat.last_modified = datetime.utcnow()
        
        session.commit()
        
        return tool_call_id
    
    except Exception as e:
        session.rollback()
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

def main():
    """Демонстрация работы с чатами в базе данных"""
    try:
        print("\n=== Демонстрация работы с чатами в базе данных ===\n")
        
        # Создаем новый чат
        chat_name = "Тестовый чат из БД"
        agent_id = "test-agent-123"
        
        print(f"Создание нового чата: {chat_name}")
        chat_id = create_new_chat(chat_name, agent_id)
        print(f"Создан чат с ID: {chat_id}")
        
        # Добавляем сообщение пользователя
        user_content = "Привет, это тестовое сообщение из базы данных!"
        print(f"\nДобавление сообщения пользователя: {user_content}")
        group_id, message_id = add_message_to_chat(
            chat_id=chat_id,
            actor_type="user",
            actor_id="user-123",
            role="user",
            content=user_content,
            task="Тестовая задача",
            analysis="Анализ пользовательского запроса",
            materials_ids=["material-1", "material-2"]
        )
        print(f"Добавлена группа сообщений с ID: {group_id}")
        print(f"Добавлено сообщение с ID: {message_id}")
        
        # Добавляем сообщение ассистента
        assistant_content = "Здравствуйте! Я получил ваше сообщение и готов помочь."
        print(f"\nДобавление сообщения ассистента: {assistant_content}")
        assistant_group_id, assistant_message_id = add_message_to_chat(
            chat_id=chat_id,
            actor_type="agent",
            actor_id="assistant-123",
            role="assistant",
            content=assistant_content,
            task="Ответ на запрос пользователя",
            analysis="Анализ и формирование ответа",
            materials_ids=["material-3"]
        )
        print(f"Добавлена группа сообщений с ID: {assistant_group_id}")
        print(f"Добавлено сообщение с ID: {assistant_message_id}")
        
        # Добавляем вызов инструмента
        tool_name = "search_database"
        tool_arguments = {"query": "тестовый запрос", "limit": 5}
        print(f"\nДобавление вызова инструмента: {tool_name}")
        tool_call_id = add_tool_call_to_message(
            message_id=assistant_message_id,
            name=tool_name,
            arguments=tool_arguments
        )
        print(f"Добавлен вызов инструмента с ID: {tool_call_id}")
        
        # Загружаем чат из базы данных
        print(f"\nЗагрузка чата с ID: {chat_id}")
        chat_data = load_chat_from_db(chat_id)
        
        # Выводим данные чата
        print("\nДанные чата:")
        print(json.dumps(chat_data, indent=2, ensure_ascii=False, default=lambda obj: obj.isoformat() if isinstance(obj, datetime) else str(obj)))
        
        # Получаем список всех чатов
        print("\nСписок всех чатов:")
        chats = list_chats()
        for chat in chats:
            print(f"ID: {chat['id']}, Название: {chat['name']}, Последнее изменение: {chat['last_modified']}")
        
        print("\nДемонстрация завершена!")
        
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main() 