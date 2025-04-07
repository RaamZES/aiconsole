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
import datetime
import logging

from aiconsole.api.websockets.connection_manager import connection_manager
from aiconsole.api.websockets.server_messages import AssetsUpdatedServerMessage
from aiconsole.core.assets.db.delete_asset_from_db import delete_asset_from_db
from aiconsole.core.assets.db.save_asset_to_db import save_asset_to_db
from aiconsole.core.assets.db.load_asset_from_db import load_asset_from_db
from aiconsole.core.assets.types import Asset, AssetLocation, AssetStatus, AssetType
from aiconsole.core.project import project
from aiconsole.core.settings.settings import settings
from aiconsole_toolkit.settings.partial_settings_data import PartialSettingsData

_log = logging.getLogger(__name__)


class Assets:
    # _assets have lists, where the 1st element is the one overriding the others
    # Currently there can be only 1 overriden element
    _assets: dict[str, list[Asset]]

    def __init__(self, asset_type: AssetType):
        self._suppress_notification_until: datetime.datetime | None = None
        self.asset_type = asset_type
        self._assets = {}

    def stop(self):
        pass  # No need to stop observer for DB

    def all_assets(self) -> list[Asset]:
        """
        Return all loaded assets.
        """
        return list(assets[0] for assets in self._assets.values())

    def assets_with_status(self, status: AssetStatus) -> list[Asset]:
        """
        Return all loaded assets with a specific status.
        """
        return [
            assets[0] for assets in self._assets.values() if self.get_status(self.asset_type, assets[0].id) == status
        ]

    async def get_asset(self, asset_id: str, location: AssetLocation | None = None) -> Asset | None:
        """
        Get a single asset by ID and optional location.
        If location is None, returns the first available asset with the given ID.
        Returns None if asset is not found.
        """
        if asset_id not in self._assets:
            # Try to load from DB if not in memory
            try:
                asset = await load_asset_from_db(self.asset_type, asset_id)
                if asset.id not in self._assets:
                    self._assets[asset.id] = []
                self._assets[asset.id].append(asset)
            except Exception as e:
                _log.debug(f"Asset {asset_id} not found in database: {e}")
                return None

        if not self._assets[asset_id]:
            return None

        if location is None:
            return self._assets[asset_id][0]

        for asset in self._assets[asset_id]:
            if asset.defined_in == location:
                return asset

        return None

    async def save_asset(self, asset: Asset, old_asset_id: str, create: bool):
        if asset.defined_in != AssetLocation.PROJECT_DIR and not create:
            raise Exception("Cannot save asset not defined in project.")

        # In DB we can always create a new asset or update an existing one
        new_asset = await save_asset_to_db(asset, old_asset_id)

        # If it's a new asset, create a new record in _assets
        if create:
            self._assets[new_asset.id] = []
        
        # If it's an update of an existing asset
        if not create:
            # Update existing asset
            if old_asset_id in self._assets:
                self._assets[old_asset_id] = []
                self._assets[old_asset_id].insert(0, new_asset)
        else:
            # Add new asset
            self._assets[new_asset.id].insert(0, new_asset)

        # Send notification that assets have been updated
        await connection_manager().send_to_all(AssetsUpdatedServerMessage(
            initial=False,
            asset_type=self.asset_type,
            count=len(self._assets)
        ))

        return False  # No rename needed for DB

    async def delete_asset(self, asset_id):
        if asset_id not in self._assets:
            raise KeyError(f"Asset {asset_id} not found")

        self._assets[asset_id].pop(0)

        if len(self._assets[asset_id]) == 0:
            del self._assets[asset_id]

        await delete_asset_from_db(self.asset_type, asset_id)

        # Send notification that assets have been updated
        await connection_manager().send_to_all(AssetsUpdatedServerMessage(
            initial=False,
            asset_type=self.asset_type,
            count=len(self._assets)
        ))

    def _suppress_notification(self):
        self._suppress_notification_until = datetime.datetime.now() + datetime.timedelta(seconds=10)

    async def reload(self, initial: bool = False):
        """
        Reload all assets from the database.
        """
        from aiconsole.core.assets.load_all_assets import load_all_assets

        # Load all assets from DB
        self._assets = await load_all_assets(self.asset_type)

        if not initial:
            await connection_manager().send_to_all(AssetsUpdatedServerMessage())

    @staticmethod
    def get_status(asset_type: AssetType, id: str) -> AssetStatus:
        if asset_type == AssetType.MATERIAL:
            return settings().get_material_status(id)
        elif asset_type == AssetType.AGENT:
            return settings().get_agent_status(id)
        else:
            raise ValueError(f"Unknown asset type {asset_type}")

    @staticmethod
    def set_status(asset_type: AssetType, id: str, status: AssetStatus, to_global: bool = False) -> None:
        if asset_type == AssetType.MATERIAL:
            settings().save(PartialSettingsData(materials={id: status}), to_global=to_global)
        elif asset_type == AssetType.AGENT:
            settings().save(PartialSettingsData(agents={id: status}), to_global=to_global)
        else:
            raise ValueError(f"Unknown asset type {asset_type}")

    @staticmethod
    def rename_asset(asset_type: AssetType, old_id: str, new_id: str):
        if asset_type == AssetType.MATERIAL:
            partial_settings = PartialSettingsData(
                materials_to_reset=[old_id],
                materials={new_id: Assets.get_status(asset_type, old_id)},
            )
        elif asset_type == AssetType.AGENT:
            partial_settings = PartialSettingsData(
                agents_to_reset=[old_id],
                agents={new_id: Assets.get_status(asset_type, old_id)},
            )
        else:
            raise ValueError(f"Unknown asset type {asset_type}")

        settings().save(partial_settings, to_global=False)
