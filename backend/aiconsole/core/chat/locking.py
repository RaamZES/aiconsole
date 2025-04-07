import asyncio
import logging
from collections import defaultdict
from typing import Callable, Coroutine

from fastapi import HTTPException

from aiconsole.api.websockets.connection_manager import (
    AICConnection,
    connection_manager,
)
from aiconsole.api.websockets.server_messages import (
    NotifyAboutChatMutationServerMessage,
)
from aiconsole.core.chat.apply_mutation import apply_mutation
from aiconsole.core.chat.chat_mutations import (
    ChatMutation,
    LockAcquiredMutation,
    LockReleasedMutation,
)
from aiconsole.core.chat.chat_mutator import ChatMutator
from aiconsole.core.chat.load_chat_history import load_chat_history
from aiconsole.core.chat.save_chat_history import save_chat_history
from aiconsole.core.chat.types import Chat

chats: dict[str, Chat] = {}
lock_events: dict[str, asyncio.Event] = defaultdict(asyncio.Event)

lock_timeout = 30  # Time in seconds to wait for the lock

_log = logging.getLogger(__name__)


async def wait_for_lock(chat_id: str) -> None:
    try:
        _log.debug(f"Waiting for lock {chat_id}")
        await asyncio.wait_for(lock_events[chat_id].wait(), timeout=lock_timeout)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Lock acquisition timed out")


async def acquire_lock(chat_id: str, request_id: str, skip_mutating_clients: bool = False):
    _log.debug(f"Acquiring lock {chat_id} {request_id}")
    if chat_id in chats and chats[chat_id].lock_id:
        await wait_for_lock(chat_id)

    if chat_id not in chats:
        chat_history = await load_chat_history(chat_id)
        if chat_history is None:
            # Create a new chat if it doesn't exist
            from datetime import datetime
            from aiconsole.core.chat.types import ChatOptions
            chat_history = Chat(
                id=chat_id,
                name="New Chat",
                title_edited=False,
                last_modified=datetime.utcnow(),
                agent_id=None,
                is_analysis_in_progress=False,
                chat_options=ChatOptions(),
                message_groups=[],
                lock_id=None
            )
        chat_history.lock_id = None
        chats[chat_id] = chat_history

    chats[chat_id].lock_id = request_id
    lock_events[chat_id].clear()

    if not skip_mutating_clients:
        await connection_manager().send_to_chat(
            NotifyAboutChatMutationServerMessage(
                request_id=request_id, chat_id=chat_id, mutation=LockAcquiredMutation(lock_id=request_id)
            ),
            chat_id,
        )
    return chats[chat_id]


async def _read_chat_outside_of_lock(chat_id: str):
    _log.debug(f"Reading chat{chat_id}")
    if chat_id not in chats:
        chat = await load_chat_history(chat_id)
        if chat is None:
            # Create a new chat if it doesn't exist
            from datetime import datetime
            from aiconsole.core.chat.types import ChatOptions
            chat = Chat(
                id=chat_id,
                name="New Chat",
                title_edited=False,
                last_modified=datetime.utcnow(),
                agent_id=None,
                is_analysis_in_progress=False,
                chat_options=ChatOptions(),
                message_groups=[],
                lock_id=None
            )
        return chat

    return chats[chat_id]


async def release_lock(chat_id: str, request_id: str) -> None:
    if chat_id in chats and chats[chat_id].lock_id == request_id:
        chats[chat_id].lock_id = None
        save_chat_history(chats[chat_id], scope="message_groups")
        del chats[chat_id]
        lock_events[chat_id].set()

        await connection_manager().send_to_chat(
            NotifyAboutChatMutationServerMessage(
                request_id=request_id, chat_id=chat_id, mutation=LockReleasedMutation(lock_id=request_id)
            ),
            chat_id,
        )


class DefaultChatMutator(ChatMutator):
    def __init__(self, chat_id: str, request_id: str, connection: AICConnection | None):
        self.chat_id = chat_id
        self.request_id = request_id
        self.connection = connection

    @property
    def chat(self) -> Chat:
        return chats[self.chat_id]

    async def mutate(self, mutation: ChatMutation) -> None:
        if self.chat_id not in chats or chats[self.chat_id].lock_id != self.request_id:
            raise Exception(
                f"Lock not acquired for chat {self.chat_id} request_id={self.request_id}",
            )

        apply_mutation(self.chat, mutation)
        
        # Save changes to database after each mutation
        save_chat_history(self.chat, scope="message_groups")

        await connection_manager().send_to_chat(
            NotifyAboutChatMutationServerMessage(
                request_id=self.request_id,
                chat_id=self.chat_id,
                mutation=mutation,
            ),
            self.chat_id,
            except_connection=self.connection,
        )


# This lock is responsible for sequencing the mutations and reads on a given chat
_waiting_mutations: dict[str, list[Coroutine]] = defaultdict(lambda: [])
_running_mutations: dict[str, asyncio.Task | None] = defaultdict(lambda: None)


def _check_mutation_queue(chat_id: str):
    if _running_mutations[chat_id] is not None:
        return

    if not _waiting_mutations[chat_id]:
        return

    h = _waiting_mutations[chat_id].pop()
    task = asyncio.create_task(h)
    _running_mutations[chat_id] = task

    def clear_task(future):
        if _running_mutations[chat_id] == future:
            _running_mutations[chat_id] = None
            _check_mutation_queue(chat_id)
        else:
            _log.error(f"Task {chat_id} already cleared")

    task.add_done_callback(clear_task)


class SequentialChatMutator(ChatMutator):
    def __init__(self, mutator: DefaultChatMutator):
        self.mutator = mutator
        self._chat = None

    @property
    def chat(self) -> Chat:
        return self.mutator.chat

    async def mutate(self, mutation: ChatMutation) -> None:
        async def h():
            await self.mutator.mutate(mutation)

        _waiting_mutations[self.mutator.chat_id].append(h())
        _check_mutation_queue(self.mutator.chat_id)

        await self.wait_for_all_mutations()

    async def wait_for_all_mutations(self):
        chat_id = self.mutator.chat_id
        while _waiting_mutations[chat_id] or _running_mutations[chat_id] is not None:
            running_mutation = _running_mutations[chat_id]
            if running_mutation:
                await running_mutation
            else:
                await asyncio.sleep(0)

    async def in_sequence(self, f: Callable[[], Coroutine]):
        _waiting_mutations[self.mutator.chat_id].append(f())
        _check_mutation_queue(self.mutator.chat_id)

    async def read(self) -> Chat:
        while True:
            running_mutation = _running_mutations[self.mutator.chat_id]

            if running_mutation is None:
                break

            await running_mutation

            if running_mutation.exception():
                _log.exception(running_mutation.exception())

            await asyncio.sleep(0)

        return await _read_chat_outside_of_lock(chat_id=self.mutator.chat_id)
