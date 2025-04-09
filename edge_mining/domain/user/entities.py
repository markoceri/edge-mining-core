"""Collection of Entities for the User Settings domain of the Edge Mining application."""

from dataclasses import dataclass, field
from typing import Dict, Any
import uuid

from edge_mining.domain.common import EntityId
from edge_mining.domain.user.common import UserId

@dataclass
class User:
    id: UserId
    username: str
    # Add password hash, roles etc. if needed

@dataclass
class SystemSettings:
    id: EntityId = field(default_factory=uuid.uuid4) # Or a fixed ID like 'global_settings'
    settings: Dict[str, Any] = field(default_factory=dict)
    # e.g., {"notification_preferences": {"telegram_chat_id": "123"}, "default_pool": "..."}

    def get_setting(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

    def set_setting(self, key: str, value: Any):
        self.settings[key] = value