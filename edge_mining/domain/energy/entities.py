"""Collection of Entities for the Energy System Monitoring domain of the Edge Mining application."""

from dataclasses import dataclass, field
import uuid

from edge_mining.domain.common import WattHours, EntityId
from edge_mining.domain.energy.common import EnergySourceType

@dataclass
class EnergySource:
    id: EntityId = field(default_factory=uuid.uuid4)
    name: str
    type: EnergySourceType # e.g., "solar", "wind", "grid"

@dataclass
class EnergyStorage:
    id: EntityId = field(default_factory=uuid.uuid4)
    name: str
    nominal_capacity: WattHours

@dataclass
class EnergyLoad:
    id: EntityId = field(default_factory=uuid.uuid4)
    name: str # e.g., "House Load"