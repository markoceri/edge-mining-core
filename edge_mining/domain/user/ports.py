"""Collection of Ports for the User Settings domain of the Edge Mining application."""

from abc import ABC, abstractmethod
from typing import Optional

from edge_mining.domain.user.common import UserId
from edge_mining.domain.user.entities import User, SystemSettings

class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: UserId) -> Optional[User]:
        raise NotImplementedError
    # ... other methods as needed

class SettingsRepository(ABC):
    @abstractmethod
    def get_settings(self) -> Optional[SystemSettings]: # Assuming single settings object
        raise NotImplementedError

    @abstractmethod
    def save_settings(self, settings: SystemSettings) -> None:
        raise NotImplementedError