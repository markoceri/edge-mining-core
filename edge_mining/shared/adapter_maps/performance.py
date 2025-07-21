"""
Collection of adapters maps for the performace tracker domain
of the Edge Mining application.
"""

from typing import Dict, Optional

from edge_mining.domain.performance.common import MiningPerformanceTrackerAdapter

from edge_mining.shared.interfaces.config import MiningPerformanceTrackerConfig
from edge_mining.shared.adapter_configs.performance import MiningPerformanceTrackerDummyConfig

MINING_PERFORMACE_TRACKER_CONFIG_TYPE_MAP: Dict[
    MiningPerformanceTrackerAdapter, Optional[MiningPerformanceTrackerConfig]
] = {
    MiningPerformanceTrackerAdapter.DUMMY: MiningPerformanceTrackerDummyConfig
}
