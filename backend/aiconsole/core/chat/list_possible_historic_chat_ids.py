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

import os
from pathlib import Path
from aiconsole.core.db.chat_db_operations import list_chats


def list_possible_historic_chat_ids(project_path: Path | None = None):
    """
    List all chat IDs from database
    
    Args:
        project_path (Path | None): Project path (not used in database version)
        
    Returns:
        list: List of chat IDs
    """
    chats = list_chats()
    return [chat["id"] for chat in chats]
