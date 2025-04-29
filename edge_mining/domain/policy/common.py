"""Collection of Common Objects for the Energy Optimization domain of the Edge Mining application."""

from dataclasses import dataclass
from enum import Enum

# Decision object
class MiningDecision(Enum):
    START_MINING = "start_mining"
    STOP_MINING = "stop_mining"
    MAINTAIN_STATE = "maintain_state"
    # Could add more granular decisions later, e.g., ADJUST_POWER

# Rule type
class RuleType(Enum):
    START = "start"
    STOP = "stop"
    # Could add more types of rules in the future