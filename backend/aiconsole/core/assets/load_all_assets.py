import os
from pathlib import Path
from sqlalchemy import select

from aiconsole.api.websockets.connection_manager import connection_manager
from aiconsole.api.websockets.server_messages import ErrorServerMessage
from aiconsole.core.assets.assets import Assets
from aiconsole.core.assets.db.load_asset_from_db import load_asset_from_db
from aiconsole.core.assets.types import Asset, AssetLocation, AssetStatus, AssetType
from aiconsole.core.assets.models import AssetModel
from aiconsole.core.assets.database import get_db


async def load_all_assets(asset_type: AssetType) -> dict[str, list[Asset]]:
    _assets: dict[str, list[Asset]] = {}
    
    async for db in get_db():
        # Get all assets of the corresponding type from DB
        result = await db.execute(
            select(AssetModel).filter(AssetModel.type == asset_type.value)
        )
        db_assets = result.scalars().all()
        
        for db_asset in db_assets:
            try:
                # Load each asset
                asset = await load_asset_from_db(asset_type, db_asset.id)

                # Legacy support (for v. prior to 0.2.11)
                if Assets.get_status(asset.type, asset.id) == AssetStatus.FORCED:
                    Assets.set_status(asset.type, asset.id, AssetStatus.ENABLED)

                if asset.id not in _assets:
                    _assets[asset.id] = []
                _assets[asset.id].append(asset)
            except Exception as e:
                await connection_manager().send_to_all(
                    ErrorServerMessage(
                        error=f"Invalid {asset_type} {db_asset.id} {e}",
                    )
                )
                continue

    return _assets
