"""Collection of Common Objects for the Mining Device Management domain of the Edge Mining application."""

from dataclasses import dataclass
from typing import NewType
from enum import Enum

MinerId = NewType("MinerId", str) # Use specific ID format if available (e.g., MAC address)

@dataclass(frozen=True)
class MinerStatus(Enum):
    UNKNOWN = "unknown"
    OFF = "off"
    ON = "on"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"