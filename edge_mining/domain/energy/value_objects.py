"""Collection of Value Objects for the Energy System Monitoring domain of the Edge Mining application."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

from edge_mining.domain.common import Watts, WattHours, Percentage, Timestamp, ValueObject

@dataclass(frozen=True)
class Battery(ValueObject):
    """Value Object for a battery."""
    nominal_capacity: WattHours

@dataclass(frozen=True)
class Grid(ValueObject):
    """Value Object for a grid."""
    contracted_power: Watts

@dataclass(frozen=True)
class LoadState(ValueObject):
    """Value Object for an energy load state."""
    current_power: Watts
    timestamp: Timestamp = field(default_factory=datetime.now)

@dataclass(frozen=True)
class BatteryState(ValueObject):
    """Value Object for a battery state."""
    state_of_charge: Percentage
    remaining_capacity: WattHours
    current_power: Watts # Positive when charging, negative when discharging
    timestamp: Timestamp = field(default_factory=datetime.now)

@dataclass(frozen=True)
class GridState(ValueObject):
    """Value Object for a grid state."""
    current_power: Watts # Positive importing, negative exporting
    timestamp: Timestamp = field(default_factory=datetime.now)

@dataclass(frozen=True)
class EnergyStateSnapshot(ValueObject):
    """Value Object for an energy state snapshot."""
    production: Watts
    consumption: LoadState # Load excluding miner
    battery: Optional[BatteryState] # Can be None if no battery is present
    grid: Optional[GridState] # Can be None if no grid is present (e.g., off-grid)
    external_source: Optional[Watts] # For example, external generator -> future use
    timestamp: Timestamp = field(default_factory=datetime.now)
