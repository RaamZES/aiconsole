from aiconsole.api.websockets.base_server_message import BaseServerMessage
from aiconsole.core.chat.chat import Chat


class ChatOpenedServerMessage(BaseServerMessage):
    chat: Chat 