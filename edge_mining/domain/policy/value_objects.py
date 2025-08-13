"""Collection of Value Objects for the Energy Optimization domain of the Edge Mining application."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from edge_mining.domain.common import ValueObject, Watts
from edge_mining.domain.energy.entities import EnergySource
from edge_mining.domain.energy.value_objects import EnergyStateSnapshot
from edge_mining.domain.forecast.aggregate_root import Forecast
from edge_mining.domain.forecast.value_objects import Sun
from edge_mining.domain.miner.entities import Miner
from edge_mining.domain.miner.value_objects import HashRate


@dataclass(frozen=True)
class DecisionalContext(ValueObject):
    """Value Object for the context of a mining decision."""

    energy_source: EnergySource
    energy_state: EnergyStateSnapshot

    forecast: Optional[Forecast]
    home_load_forecast: Optional[Watts]

    tracker_current_hashrate: Optional[HashRate]

    sun: Optional[Sun] = field(default=None)

    miner: Optional[Miner] = field(default=None)
    timestamp: datetime = field(default_factory=datetime.now)
