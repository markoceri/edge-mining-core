"""Collection of Ports for the Mining Device Management domain of the Edge Mining application."""

from abc import ABC, abstractmethod
from typing import Optional, List

from edge_mining.domain.common import Watts
from edge_mining.domain.miner.entities import Miner
from edge_mining.domain.miner.common import MinerId, MinerStatus

class MinerControlPort(ABC):
    @abstractmethod
    def start_miner(self, miner_id: MinerId) -> bool:
        """Attempts to start the specified miner. Returns True on success request."""
        raise NotImplementedError

    @abstractmethod
    def stop_miner(self, miner_id: MinerId) -> bool:
        """Attempts to stop the specified miner. Returns True on success request."""
        raise NotImplementedError

    @abstractmethod
    def get_miner_status(self, miner_id: MinerId) -> MinerStatus:
        """Gets the current operational status of the miner."""
        raise NotImplementedError

    @abstractmethod
    def get_miner_power(self, miner_id: MinerId) -> Optional[Watts]:
        """Gets the current power consumption, if available."""
        raise NotImplementedError

class MinerRepository(ABC):
    @abstractmethod
    def add(self, miner: Miner) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, miner_id: MinerId) -> Optional[Miner]:
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> List[Miner]:
        raise NotImplementedError

    @abstractmethod
    def update(self, miner: Miner) -> None:
        raise NotImplementedError

    @abstractmethod
    def remove(self, miner_id: MinerId) -> None:
        raise NotImplementedError