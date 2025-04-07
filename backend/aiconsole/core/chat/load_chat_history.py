from pathlib import Path
from aiconsole.core.chat.types import Chat, ChatOptions, AICMessageGroup, AICMessage, AICToolCall
from aiconsole.core.db.chat_db_operations import load_chat_from_db

async def load_chat_history(id: str, project_path: Path | None = None):
    """
    Load chat history from database
    
    Args:
        id (str): Chat ID
        project_path (Path | None): Project path (not used in database version)
        
    Returns:
        Chat | None: Chat object or None if not found
    """
    # Load chat data from database
    chat_data = load_chat_from_db(id)
    
    if not chat_data:
        return None
    
    # Create Chat object from data
    chat = Chat(
        id=chat_data["id"],
        name=chat_data["name"],
        title_edited=chat_data["title_edited"],
        last_modified=chat_data["last_modified"],
        chat_options=ChatOptions(**chat_data["chat_options"]),
        is_analysis_in_progress=chat_data["is_analysis_in_progress"],
        message_groups=[],
        lock_id=None
    )
    
    # Add message groups
    for group_data in chat_data["message_groups"]:
        group = AICMessageGroup(
            id=group_data["id"],
            actor_id=group_data["actor_id"],
            role=group_data["role"],
            task=group_data["task"],
            analysis=group_data["analysis"],
            materials_ids=group_data["materials_ids"],
            messages=[]
        )
        
        # Add messages
        for message_data in group_data["messages"]:
            message = AICMessage(
                id=message_data["id"],
                content=message_data["content"],
                timestamp=message_data["timestamp"],
                requested_format=message_data["requested_format"],
                is_streaming=message_data["is_streaming"],
                tool_calls=[]
            )
            
            # Add tool calls
            for tool_call_data in message_data["tool_calls"]:
                tool_call = AICToolCall(
                    id=tool_call_data["id"],
                    name=tool_call_data["name"],
                    arguments=tool_call_data["arguments"]
                )
                message.tool_calls.append(tool_call)
            
            group.messages.append(message)
        
        chat.message_groups.append(group)
    
    return chat 