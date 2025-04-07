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
from fastapi import APIRouter, Response, status
from aiconsole.core.db.chat_db_operations import delete_chat

from aiconsole.core.chat.load_chat_history import load_chat_history
from aiconsole.core.chat.save_chat_history import save_chat_history
from aiconsole.core.project.paths import get_history_directory

router = APIRouter()


@router.delete("/{chat_id}")
async def delete_history(chat_id: str):
    try:
        delete_chat(chat_id)
        return Response(
            status_code=status.HTTP_200_OK,
            content="Chat history deleted successfully",
        )
    except Exception as e:
        return Response(
            status_code=status.HTTP_404_NOT_FOUND,
            content="Chat history not found",
        )


@router.get("/{chat_id}/path")
async def get_history_path(chat_id: str):
    return {"path": f"database://{chat_id}"}


@router.patch("/{chat_id}")
async def chat_options(chat_id: str, chat_odj: dict):
    chat = await load_chat_history(id=chat_id)
    if chat_odj.get("name"):
        chat.name = str(chat_odj.get("name"))
        save_chat_history(chat, scope="name")
    return Response(status_code=status.HTTP_200_OK)
