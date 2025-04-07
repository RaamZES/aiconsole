from fastapi import UploadFile
import os
from pathlib import Path

from aiconsole.core.assets.agents.agent import AICAgent
from aiconsole.core.assets.assets import Assets
from aiconsole.core.assets.materials.material import Material
from aiconsole.core.assets.types import Asset, AssetType, AssetLocation
from aiconsole.core.project import project
from aiconsole.core.project.paths import get_project_assets_directory


class AssetWithGivenNameAlreadyExistError(Exception):
    pass


class _Assets:
    async def _create(self, assets: Assets, asset_id: str, asset: Asset) -> None:
        await self._validate_existance(assets, asset_id)
        
        # Set correct location for new asset
        asset.defined_in = AssetLocation.PROJECT_DIR
        
        await assets.save_asset(asset, old_asset_id=asset_id, create=True)

    async def _partially_update(self, assets: Assets, old_asset_id: str, asset: Asset) -> None:
        # Check asset existence before update
        existing_asset = await assets.get_asset(old_asset_id)
        if existing_asset is None:
            raise Exception(f"Asset {old_asset_id} not found")
            
        # Save existing location
        asset.defined_in = existing_asset.defined_in
        
        await assets.save_asset(asset, old_asset_id=old_asset_id, create=False)

    async def _validate_existance(self, assets: Assets, asset_id: str) -> None:
        try:
            existing_asset = await assets.get_asset(asset_id)
            if existing_asset is not None:
                raise AssetWithGivenNameAlreadyExistError()
        except Exception as e:
            if not isinstance(e, AssetWithGivenNameAlreadyExistError):
                # If asset not found, it's normal - we can create a new one
                pass
            else:
                raise


class Agents(_Assets):
    async def create_agent(self, agent_id: str, agent: AICAgent) -> None:
        agents = project.get_project_agents()
        await self._create(agents, agent_id, agent)

    async def partially_update_agent(self, agent_id: str, agent: AICAgent) -> None:
        agents = project.get_project_agents()
        await self._partially_update(agents, agent_id, agent)

    async def set_agent_avatar(self, agent_id: str, avatar: UploadFile) -> None:
        # Create directory for avatars if it doesn't exist
        avatar_dir = get_project_assets_directory(AssetType.AGENT)
        avatar_dir.mkdir(parents=True, exist_ok=True)
        
        # Save avatar
        image_path = avatar_dir / f"{agent_id}.jpg"
        content = await avatar.read()
        with open(image_path, "wb+") as avatar_file:
            avatar_file.write(content)


class Materials(_Assets):
    async def create_material(self, material_id: str, material: Material) -> None:
        materials = project.get_project_materials()
        await self._create(materials, material_id, material)

    async def partially_update_material(self, material_id: str, material: Material) -> None:
        materials = project.get_project_materials()
        await self._partially_update(materials, material_id, material)
