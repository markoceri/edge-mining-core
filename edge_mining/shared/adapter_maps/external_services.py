"""Collection of adapters maps for the external services of the Edge Mining application."""

from typing import Dict, Optional

from edge_mining.shared.external_services.common import ExternalServiceAdapter
from edge_mining.shared.interfaces.config import ExternalServiceConfig
from edge_mining.shared.adapter_configs.external_services import (
    ExternalServiceHomeAssistantConfig,
)

EXTERNAL_SERVICE_CONFIG_TYPE_MAP: Dict[
    ExternalServiceAdapter, Optional[ExternalServiceConfig]
] = {
    ExternalServiceAdapter.HOME_ASSISTANT_API: ExternalServiceHomeAssistantConfig
}