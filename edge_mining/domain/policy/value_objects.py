"""Collection of Value Objects for the Energy Optimization domain of the Edge Mining application."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

from edge_mining.domain.common import Watts, ValueObject
from edge_mining.domain.energy.entities import EnergySource
from edge_mining.domain.energy.value_objects import EnergyStateSnapshot
from edge_mining.domain.miner.entities import Miner
from edge_mining.domain.miner.value_objects import HashRate
from edge_mining.domain.forecast.value_objects import ForecastData

@dataclass(frozen=True)
class DecisionalContext(ValueObject):
    """Value Object for the context of a mining decision."""
    energy_source: EnergySource
    energy_state: EnergyStateSnapshot

    miner: Miner

    forecast: Optional[ForecastData]
    home_load_forecast: Optional[Watts]

    tracker_current_hashrate: Optional[HashRate]

    timestamp: datetime = field(default_factory=datetime.now)
