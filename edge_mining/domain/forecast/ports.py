"""Collection of Ports for the Energy Forecast domain of the Edge Mining application."""

from abc import ABC, abstractmethod
from typing import Optional

from edge_mining.domain.forecast.value_objects import ForecastData

class ForecastProviderPort(ABC):
    @abstractmethod
    def get_solar_forecast(self, latitude: Optional[float], longitude: Optional[float], capacity_kwp: Optional[float]) -> Optional[ForecastData]:
        """Fetches the solar energy production forecast."""
        raise NotImplementedError