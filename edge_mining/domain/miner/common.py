"""Collection of Common Objects for the Mining Device Management domain of the Edge Mining application."""

from dataclasses import dataclass
from typing import NewType
from enum import Enum
import uuid

MinerId = NewType("MinerId", uuid.UUID)

class MinerStatus(Enum):
    """Enum for the different miner statuses."""
    UNKNOWN = "unknown"
    OFF = "off"
    ON = "on"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"