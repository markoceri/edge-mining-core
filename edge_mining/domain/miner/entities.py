"""Collection of Entities for the Mining Device Management domain of the Edge Mining application."""

from dataclasses import dataclass
from typing import Optional

from edge_mining.domain.common import Watts
from edge_mining.domain.miner.common import MinerId, MinerStatus

@dataclass
class Miner:
    id: MinerId
    name: str
    status: MinerStatus = MinerStatus.UNKNOWN
    power_consumption: Optional[Watts] = None # Can be dynamic or fixed
    ip_address: Optional[str] = None # 🤷​ Will need it for some control methods ?
    # Potentially add more details: model, location, etc. but for now, I think this is enough

    def turn_on(self):
        # Domain logic: update status if applicable
        if self.status in [MinerStatus.OFF, MinerStatus.ERROR, MinerStatus.UNKNOWN]:
            self.status = MinerStatus.STARTING
            print(f"Domain: Miner {self.id} requested to turn ON") # Placeholder
        # Else: Already on or transitioning

    def turn_off(self):
        # Domain logic: update status if applicable
        if self.status in [MinerStatus.ON, MinerStatus.ERROR]:
            self.status = MinerStatus.STOPPING
            print(f"Domain: Miner {self.id} requested to turn OFF") # Placeholder
        # Else: Already off or transitioning

    def update_status(self, new_status: MinerStatus, power: Optional[Watts] = None):
        self.status = new_status
        if power is not None:
            self.power_consumption = power
        print(f"Domain: Miner {self.id} status updated to {new_status}, power: {power}") # Placeholder