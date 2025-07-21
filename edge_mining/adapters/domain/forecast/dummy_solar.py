"""
Dummy adapter (Implementation of Port) that simulates
the energy forecast for Edge Mining Application
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import random

from edge_mining.domain.common import Watts, Timestamp
from edge_mining.domain.energy.entities import EnergySource
from edge_mining.domain.forecast.common import ForecastProviderAdapter
from edge_mining.domain.forecast.ports import ForecastProviderPort
from edge_mining.domain.forecast.value_objects import ForecastData
from edge_mining.domain.forecast.exceptions import (
    ForecastError
)

from edge_mining.shared.logging.port import LoggerPort
from edge_mining.shared.external_services.ports import ExternalServicePort
from edge_mining.shared.interfaces.config import ForecastProviderConfig
from edge_mining.shared.interfaces.factories import ForecastAdapterFactory
from edge_mining.shared.adapter_configs.forecast import ForecastProviderDummySolarConfig

class DummyForecastProviderFactory(ForecastAdapterFactory):
    """
    Factory for creating a DummySolarForecastProvider instance.
    """
    def __init__(self):
        self._energy_source: EnergySource = None

    def from_energy_source(self, energy_source: EnergySource) -> None:
        """Set the reference energy source"""
        self._energy_source = energy_source

    def create(
        self,
        config: ForecastProviderConfig,
        logger: LoggerPort,
        external_service: ExternalServicePort
    ) -> ForecastProviderPort:
        """
        Creates a DummySolarForecastProvider instance.
        """
        if not isinstance(config, ForecastProviderDummySolarConfig):
            raise ForecastError("Invalid configuration type for HomeAssistantAPI forecast provider. "
                                "Expected ForecastProviderDummySolarConfig.")

        # Get the config from the forecast provider config
        forecast_provider_config: ForecastProviderDummySolarConfig = config

        if not forecast_provider_config.capacity_kwp:
            if self._energy_source and self._energy_source.nominal_power_max:
                forecast_provider_config.capacity_kwp = self._energy_source.nominal_power_max

        return DummySolarForecastProvider(
            latitude=forecast_provider_config.latitude,
            longitude=forecast_provider_config.longitude,
            capacity_kwp=forecast_provider_config.capacity_kwp,
            logger=logger
        )

class DummySolarForecastProvider(ForecastProviderPort):
    """Dummy implementation of the ForecastProviderPort."""
    def __init__(
        self,
        latitude: float = None,
        longitude: float = None,
        capacity_kwp: float = 0.0,
        logger: LoggerPort = None
    ):
        """Initializes the DummySolarForecastProvider."""
        super().__init__(forecast_provider_type=ForecastProviderAdapter.DUMMY_SOLAR)
        self.logger = logger

        self.latitude = latitude
        self.longitude = longitude
        self.capacity_kwp = capacity_kwp
        # You can set default values or use the ones from settings if needed

    def get_solar_forecast(self) -> Optional[ForecastData]:
        # Generates a plausible fake solar forecast.
        if self.logger:
            self.logger.debug(f"DummySolarForecastProvider: "
                            f"Generating forecast for {self.latitude},{self.longitude} "
                            f"({self.capacity_kwp} kWp)")
        now = datetime.now()
        predictions: Dict[Timestamp, Watts] = {}
        base_max_watts = self.capacity_kwp * 1000 * 0.8 # Assume 80% peak efficiency

        for i in range(24): # Forecast for next 24 hours
            future_time = now + timedelta(hours=i)
            hour = future_time.hour

            if 6 < hour < 20:
                # Simple sinusoidal based on hour
                solar_factor = max(0, 1 - abs(hour - 13) / 7)
                # Add some randomness
                noise = random.uniform(0.7, 1.0)
                predicted_power = Watts(base_max_watts * solar_factor * noise)
            else:
                predicted_power = Watts(0.0)

            predictions[Timestamp(future_time)] = predicted_power

        forecast = ForecastData(
            predicted_power=predictions,
            generated_at=Timestamp(now)
        )
        if self.logger:
            self.logger.debug(f"DummyForecastProvider: Generated {len(predictions)} predictions.")
        return forecast
