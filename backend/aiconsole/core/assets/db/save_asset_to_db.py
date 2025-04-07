from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import uuid
from aiconsole.core.assets.agents.agent import AICAgent
from aiconsole.core.assets.fs.exceptions import UserIsAnInvalidAgentIdError
from aiconsole.core.assets.materials.material import Material
from aiconsole.core.assets.types import Asset, AssetLocation
from aiconsole.core.assets.models import AssetModel
from aiconsole.core.assets.database import get_db

_USER_AGENT_ID = "user"

async def save_asset_to_db(asset: Asset, old_asset_id: str) -> Asset:
    if isinstance(asset, AICAgent):
        if asset.id == _USER_AGENT_ID:
            raise UserIsAnInvalidAgentIdError()

    async for db in get_db():
        # Get current version
        result = await db.execute(
            select(AssetModel).filter(AssetModel.id == old_asset_id)
        )
        db_asset = result.scalar_one_or_none()
        
        # If asset exists and it's not a new creation
        if db_asset:
            # Increase version
            current_version_parts = db_asset.version.split(".")
            current_version_parts[-1] = str(int(current_version_parts[-1]) + 1)
            asset.version = ".".join(current_version_parts)
            # Save old ID when updating
            asset.id = old_asset_id
        else:
            # Create new asset
            db_asset = AssetModel()
            asset.version = "0.0.1"  # Initial version for new asset
            # Always generate new ID for new assets
            prefix = "agent_" if isinstance(asset, AICAgent) else "material_"
            asset.id = f"{prefix}{str(uuid.uuid4())[:8]}"

        # Update fields
        db_asset.id = asset.id
        db_asset.type = asset.type.value
        db_asset.name = asset.name
        db_asset.version = asset.version
        db_asset.usage = asset.usage
        db_asset.usage_examples = json.dumps(asset.usage_examples)  # Serialize to JSON
        db_asset.default_status = asset.default_status.value
        db_asset.defined_in = asset.defined_in.value

        if isinstance(asset, Material):
            db_asset.content_type = asset.content_type.value
            db_asset.content = asset.content
        elif isinstance(asset, AICAgent):
            db_asset.system = asset.system if hasattr(asset, 'system') else None
            db_asset.gpt_mode = str(asset.gpt_mode) if hasattr(asset, 'gpt_mode') and asset.gpt_mode else None
            db_asset.execution_mode = asset.execution_mode if hasattr(asset, 'execution_mode') else None

        # Save to DB
        if not db_asset.id:
            db.add(db_asset)
        else:
            db.add(db_asset)  # Add existing asset to session for update
        await db.commit()  # Add commit to save changes

        return asset 