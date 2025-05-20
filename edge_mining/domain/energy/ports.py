"""Collection of Ports for the Energy System Monitoring domain of the Edge Mining application."""

from abc import ABC, abstractmethod
from typing import Optional

from edge_mining.domain.energy.value_objects import EnergyStateSnapshot

class EnergyMonitorPort(ABC):
    """Port for the Energy Monitor."""
    @abstractmethod
    def get_current_energy_state(self) -> Optional[EnergyStateSnapshot]:
        """Fetches the latest energy readings from the plant."""
        raise NotImplementedError