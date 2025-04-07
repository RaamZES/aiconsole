from aiconsole.api.websockets.base_server_message import BaseServerMessage
from aiconsole.core.assets.types import AssetType


class AssetsUpdatedServerMessage(BaseServerMessage):
    initial: bool
    asset_type: AssetType
    count: int 