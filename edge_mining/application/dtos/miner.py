"""Collection of DTOs for the miner domain"""

from typing import Optional
from enum import Enum

from edge_mining.domain.common import Watts
from edge_mining.domain.miner.common import MinerId, MinerStatus

class MinerDTO:
    id: MinerId
    name: str
    status: MinerStatus
    # power_consumption: Optional[Watts]
    ip_address: Optional[str]

    def __init__(self,
            id: MinerId,
            name: str,
            status: MinerStatus,
            #power_consumption: Optional[Watts] = None,
            ip_address: Optional[str] = None
        ):
        self.id = id
        self.name = name
        self.status = status
        #self.power_consumption = power_consumption
        self.ip_address = ip_address