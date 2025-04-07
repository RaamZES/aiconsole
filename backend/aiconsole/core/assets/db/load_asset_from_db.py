from sqlalchemy import select
import json
from sqlalchemy.ext.asyncio import AsyncSession
from aiconsole.core.assets.agents.agent import AICAgent
from aiconsole.core.assets.fs.exceptions import UserIsAnInvalidAgentIdError
from aiconsole.core.assets.materials.material import Material, MaterialContentType
from aiconsole.core.assets.types import Asset, AssetLocation, AssetStatus, AssetType
from aiconsole.core.gpt.consts import GPTMode
from aiconsole.core.assets.models import AssetModel
from aiconsole.core.assets.database import get_db

_USER_AGENT_ID = "user"

async def load_asset_from_db(asset_type: AssetType, asset_id: str, location: AssetLocation | None = None) -> Asset:
    if asset_type == AssetType.AGENT:
        if asset_id == _USER_AGENT_ID:
            raise UserIsAnInvalidAgentIdError()

    async for db in get_db():
        result = await db.execute(
            select(AssetModel).filter(AssetModel.id == asset_id)
        )
        db_asset = result.scalar_one_or_none()
        if not db_asset:
            raise KeyError(f"Asset {asset_id} not found")

        params = {
            "id": db_asset.id,
            "name": db_asset.name,
            "version": db_asset.version,
            "defined_in": location or AssetLocation.PROJECT_DIR,
            "usage": db_asset.usage,
            "usage_examples": json.loads(db_asset.usage_examples),
            "default_status": AssetStatus(db_asset.default_status),
            "override": False,  # In DB this is not as important as in FS
        }

        if asset_type == AssetType.MATERIAL:
            material = Material(
                **params,
                content_type=MaterialContentType(db_asset.content_type),
                content=db_asset.content
            )
            return material
        elif asset_type == AssetType.AGENT:
            agent = AICAgent(
                **params,
                system=db_asset.system if db_asset.system else "",
                gpt_mode=GPTMode(db_asset.gpt_mode) if db_asset.gpt_mode else None,
                execution_mode=db_asset.execution_mode if db_asset.execution_mode else "aiconsole.core.chat.execution_modes.normal:execution_mode"
            )
            return agent
        else:
            raise ValueError(f"Unknown asset type: {asset_type}") 