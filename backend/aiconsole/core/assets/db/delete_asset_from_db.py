from sqlalchemy import select
from aiconsole.core.assets.types import AssetType
from aiconsole.core.assets.models import AssetModel
from aiconsole.core.assets.database import get_db

async def delete_asset_from_db(asset_type: AssetType, id: str):
    """
    Delete a specific asset from the database.
    """
    async for db in get_db():
        result = await db.execute(
            select(AssetModel).filter(AssetModel.id == id)
        )
        db_asset = result.scalar_one_or_none()
        if db_asset:
            await db.delete(db_asset) 