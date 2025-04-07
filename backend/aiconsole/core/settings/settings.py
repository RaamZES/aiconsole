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

import logging
from functools import lru_cache

from aiconsole.core.settings.fs.settings_file_storage import SettingsUpdatedEvent
from aiconsole.core.settings.settings_notifications import SettingsNotifications
from aiconsole.core.settings.settings_storage import SettingsStorage
from aiconsole.core.settings.utils.merge_settings_data import merge_settings_data
from aiconsole.utils.events import internal_events
from aiconsole_toolkit.settings.partial_settings_data import PartialSettingsData
from aiconsole_toolkit.settings.settings_data import SettingsData
from aiconsole.core.assets.types import AssetStatus

_log = logging.getLogger(__name__)


class Settings:
    _storage: SettingsStorage | None = None
    _settings_notifications: SettingsNotifications | None = None

    def configure(self, storage: SettingsStorage):
        self.destroy()

        self._storage = storage
        self._settings_notifications = SettingsNotifications()

        internal_events().subscribe(
            SettingsUpdatedEvent,
            self._when_reloaded,
        )

        _log.info("Settings configured")

    def destroy(self):
        self._storage = None
        self._settings_notifications = None

        internal_events().unsubscribe(
            SettingsUpdatedEvent,
            self._when_reloaded,
        )

    async def _when_reloaded(self, SettingsUpdatedEvent):
        if not self._storage or not self._settings_notifications:
            raise ValueError("Settings not configured")

        await self._settings_notifications.notify()

    @property
    def unified_settings(self) -> SettingsData:
        if not self._storage or not self._settings_notifications:
            raise ValueError("Settings not configured")

        return merge_settings_data(SettingsData(), self._storage.global_settings, self._storage.project_settings)

    def save(self, settings_data: PartialSettingsData, to_global: bool):
        if not self._storage or not self._settings_notifications:
            raise ValueError("Settings not configured")

        self._settings_notifications.suppress_next_notification()
        self._storage.save(settings_data, to_global=to_global)

    def get_material_status(self, material_id: str) -> AssetStatus:
        if not self._storage:
            raise ValueError("Settings not configured")

        project_settings = self._storage.project_settings
        if project_settings and hasattr(project_settings, 'materials') and project_settings.materials and material_id in project_settings.materials:
            return project_settings.materials[material_id]

        global_settings = self._storage.global_settings
        if global_settings and hasattr(global_settings, 'materials') and global_settings.materials and material_id in global_settings.materials:
            return global_settings.materials[material_id]

        return AssetStatus.ENABLED

    def get_agent_status(self, agent_id: str) -> AssetStatus:
        if not self._storage:
            raise ValueError("Settings not configured")

        project_settings = self._storage.project_settings
        if project_settings and hasattr(project_settings, 'agents') and project_settings.agents and agent_id in project_settings.agents:
            return project_settings.agents[agent_id]

        global_settings = self._storage.global_settings
        if global_settings and hasattr(global_settings, 'agents') and global_settings.agents and agent_id in global_settings.agents:
            return global_settings.agents[agent_id]

        return AssetStatus.ENABLED


@lru_cache
def settings() -> Settings:
    return Settings()
