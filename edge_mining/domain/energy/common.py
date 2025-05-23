"""Collection of Common Objects for the Energy System Monitoring domain of the Edge Mining application."""

from enum import Enum
from typing import NewType
import uuid

EnergyMonitorId = NewType("EnergyMonitorId", uuid.UUID)

class EnergySourceType(Enum):
    """Enum for the different energy sources."""
    SOLAR = "solar"
    WIND = "wind"
    GRID = "grid"
    HYDROELECTRIC = "hydroelectric"
    OTHER = "other"

class EnergyMonitorAdapter(Enum):
    """Enum for the different energy monitor adapters."""
    DUMMY = "dummy"
    HOME_ASSISTANT_API = "home_assistant_api"
