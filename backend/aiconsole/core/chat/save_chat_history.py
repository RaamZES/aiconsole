# The AIConsole Project
#
# Copyright 2023 10Clouds
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime
from aiconsole.core.chat.types import Chat
from aiconsole.core.db.chat_db_operations import save_chat_to_db

def save_chat_history(chat: Chat, scope: str = "default"):
    """
    Save chat history to database
    
    Args:
        chat (Chat): Chat object to save
        scope (str): Scope of the save operation
    """
    # Update last_modified
    chat.last_modified = datetime.utcnow()
    
    # Convert Chat object to dictionary
    chat_data = {
        "id": chat.id,
        "name": chat.name,
        "title_edited": chat.title_edited,
        "last_modified": chat.last_modified.isoformat() if chat.last_modified else None,
        "chat_options": chat.chat_options.model_dump() if chat.chat_options else {},
        "is_analysis_in_progress": chat.is_analysis_in_progress,
        "message_groups": []
    }
    
    # Add message groups
    for group in chat.message_groups:
        group_data = {
            "id": group.id,
            "actor_id": group.actor_id.model_dump() if hasattr(group.actor_id, 'model_dump') else group.actor_id,
            "role": group.role,
            "task": group.task,
            "analysis": group.analysis,
            "materials_ids": group.materials_ids,
            "messages": []
        }
        
        # Add messages
        for message in group.messages:
            message_data = {
                "id": message.id,
                "content": message.content,
                "timestamp": message.timestamp,  # timestamp is already a string
                "requested_format": message.requested_format,
                "is_streaming": message.is_streaming,
                "tool_calls": []
            }
            
            # Add tool calls
            for tool_call in message.tool_calls:
                tool_call_data = {
                    "id": tool_call.id,
                    "name": tool_call.name,
                    "arguments": tool_call.arguments
                }
                message_data["tool_calls"].append(tool_call_data)
            
            group_data["messages"].append(message_data)
        
        chat_data["message_groups"].append(group_data)
    
    # Save to database
    save_chat_to_db(chat_data)
