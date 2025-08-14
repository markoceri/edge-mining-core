"""
This service is responsible for creating and managing adapters for the application.
"""

from typing import Any, Dict, List, Optional

from edge_mining.adapters.domain.energy.dummy_solar import DummySolarEnergyMonitorFactory
from edge_mining.adapters.domain.energy.home_assistant_api import HomeAssistantAPIEnergyMonitorFactory
from edge_mining.adapters.domain.forecast.dummy_solar import DummyForecastProviderFactory
from edge_mining.adapters.domain.forecast.home_assistant_api import HomeAssistantForecastProviderFactory
from edge_mining.adapters.domain.home_load.dummy import DummyHomeForecastProvider
from edge_mining.adapters.domain.miner.dummy import DummyMinerController
from edge_mining.adapters.domain.notification.dummy import DummyNotifier
from edge_mining.adapters.domain.notification.telegram import TelegramNotifierFactory
from edge_mining.adapters.domain.performance.dummy import DummyMiningPerformanceTracker
from edge_mining.adapters.infrastructure.homeassistant.homeassistant_api import ServiceHomeAssistantAPIFactory
from edge_mining.adapters.infrastructure.rule_engine.factory import RuleEngineFactory
from edge_mining.application.interfaces import AdapterServiceInterface
from edge_mining.domain.common import EntityId
from edge_mining.domain.energy.common import EnergyMonitorAdapter
from edge_mining.domain.energy.entities import EnergyMonitor, EnergySource
from edge_mining.domain.energy.ports import EnergyMonitorPort, EnergyMonitorRepository
from edge_mining.domain.forecast.common import ForecastProviderAdapter
from edge_mining.domain.forecast.entities import ForecastProvider
from edge_mining.domain.forecast.ports import ForecastProviderPort, ForecastProviderRepository
from edge_mining.domain.home_load.common import HomeForecastProviderAdapter
from edge_mining.domain.home_load.entities import HomeForecastProvider
from edge_mining.domain.home_load.ports import HomeForecastProviderPort, HomeForecastProviderRepository
from edge_mining.domain.miner.common import MinerControllerAdapter
from edge_mining.domain.miner.entities import Miner, MinerController
from edge_mining.domain.miner.ports import MinerControllerRepository, MinerControlPort
from edge_mining.domain.notification.common import NotificationAdapter
from edge_mining.domain.notification.entities import Notifier
from edge_mining.domain.notification.ports import NotificationPort, NotifierRepository
from edge_mining.domain.performance.common import MiningPerformanceTrackerAdapter
from edge_mining.domain.performance.entities import MiningPerformanceTracker
from edge_mining.domain.performance.ports import MiningPerformanceTrackerPort, MiningPerformanceTrackerRepository
from edge_mining.domain.policy.services import RuleEngine
from edge_mining.shared.external_services.common import ExternalServiceAdapter
from edge_mining.shared.external_services.entities import ExternalService
from edge_mining.shared.external_services.ports import ExternalServicePort, ExternalServiceRepository
from edge_mining.shared.interfaces.factories import (
    EnergyMonitorAdapterFactory,
    ExternalServiceFactory,
    ForecastAdapterFactory,
)
from edge_mining.shared.logging.port import LoggerPort


class AdapterService(AdapterServiceInterface):
    """
    This service is responsible for creating and managing adapters for the application.
    """

    def __init__(
        self,
        energy_monitor_repo: EnergyMonitorRepository,
        miner_controller_repo: MinerControllerRepository,
        notifier_repo: NotifierRepository,
        forecast_provider_repo: ForecastProviderRepository,
        mining_performance_tracker_repo: MiningPerformanceTrackerRepository,
        home_forecast_provider_repo: HomeForecastProviderRepository,
        external_service_repo: ExternalServiceRepository,
        logger: Optional[LoggerPort] = None,
    ):
        self.energy_monitor_repo = energy_monitor_repo
        self.miner_controller_repo = miner_controller_repo
        self.notifier_repo = notifier_repo
        self.forecast_provider_repo = forecast_provider_repo
        self.mining_performance_tracker_repo = mining_performance_tracker_repo
        self.home_forecast_provider_repo = home_forecast_provider_repo
        self.external_service_repo = external_service_repo
        self._instance_cache: Dict[EntityId, Any] = {}  # Cache for already created instances
        self._service_cache: Dict[EntityId, ExternalServicePort] = {}  # Cache for already created external services

        self.logger = logger

    def _initialize_external_service(self, external_service: ExternalService) -> Optional[ExternalServicePort]:
        """Initialize an external service"""
        # If the external service already exists, we use it
        if external_service.id in self._service_cache:
            self.logger.debug(
                f"Returning cached instance "
                f"for external service ID {external_service.id} "
                f"(Type: {external_service.adapter_type})"
            )
            return self._service_cache[external_service.id]

        try:
            external_service_factory: ExternalServiceFactory = None

            if external_service.adapter_type == ExternalServiceAdapter.HOME_ASSISTANT_API.value:
                # --- Home Assistant API ---

                external_service_factory = ServiceHomeAssistantAPIFactory()
            else:
                raise ValueError(f"Unsupported external service type: " f"{external_service.adapter_type}")

            instance_service = external_service_factory.create(config=external_service.config, logger=self.logger)

            self._service_cache[external_service.id] = instance_service
            return instance_service
        except Exception as e:
            self.logger.error(
                f"Failed to initialize External Service '{external_service.name}' "
                f"(Type: {external_service.adapter_type}): {e}"
            )
            return None

    def _initialize_energy_monitor_adapter(
        self, energy_source: EnergySource, energy_monitor: EnergyMonitor
    ) -> Optional[EnergyMonitorPort]:
        """Initialize an energy monitor adapter."""
        # If the adapter has already been created, we use it.
        if energy_monitor.id in self._instance_cache:
            self.logger.debug(
                f"Returning cached adapter instance "
                f"for energy monitor ID {energy_monitor.id} "
                f"(Type: {energy_monitor.adapter_type})"
            )
            return self._instance_cache[energy_monitor.id]

        # Retrieve the external service associated to the energy monitor
        if energy_monitor.external_service_id:
            external_service = self.get_external_service(energy_monitor.external_service_id)
            if not external_service:
                raise ValueError(
                    f"Unable to load external service {energy_monitor.external_service_id} "
                    f"for energy monitor {energy_monitor.name}"
                )

        try:
            energy_monitor_adapter_factory: EnergyMonitorAdapterFactory = None

            if energy_monitor.adapter_type == EnergyMonitorAdapter.DUMMY_SOLAR.value:
                # --- Dummy Solar ---
                if not energy_source:
                    raise ValueError("EnergySource is required for DummySolar energy monitor.")

                energy_monitor_adapter_factory = DummySolarEnergyMonitorFactory()

                # Set energy source as reference
                energy_monitor_adapter_factory.from_energy_source(energy_source)
            elif energy_monitor.adapter_type == EnergyMonitorAdapter.HOME_ASSISTANT_API.value:
                # --- Home Assistant API ---
                if not energy_monitor.config:
                    raise ValueError("EnergyMonitor config is required " "for HomeAssistantAPI energy monitor.")

                energy_monitor_adapter_factory = HomeAssistantAPIEnergyMonitorFactory()
                # Actually HomeAssistantAPI Energy Monitor
                # does not needs an energy source as reference
            else:
                raise ValueError(f"Unsupported energy monitor adapter type: " f"{energy_monitor.adapter_type}")

            instance = energy_monitor_adapter_factory.create(
                config=energy_monitor.config,
                logger=self.logger,
                external_service=external_service,
            )

            self._instance_cache[energy_monitor.id] = instance
            return instance
        except Exception as e:
            self.logger.error(
                f"Failed to initialize adapter '{energy_monitor.name}' "
                f"(Type: {energy_monitor.adapter_type}) using factory: {e}"
            )
            return None

    def _initialize_miner_controller_adapter(
        self, miner: Miner, miner_controller: MinerController
    ) -> Optional[MinerControlPort]:
        """Initialize a miner controller adapter."""
        # If the adapter has already been created, we use it.
        if miner_controller.id in self._instance_cache:
            self.logger.debug(
                f"Returning cached adapter instance "
                f"for miner controller ID {miner_controller.id} "
                f"(Type: {miner_controller.adapter_type})"
            )
            return self._instance_cache[miner_controller.id]

        try:

            if miner_controller.adapter_type == MinerControllerAdapter.DUMMY.name:
                # --- Dummy Conctroller ---
                instance = DummyMinerController(
                    power_max=miner.power_consumption_max,
                    hashrate_max=miner.hash_rate_max,
                    logger=self.logger,
                )
            else:
                raise ValueError(f"Unsupported miner controller adapter type: {miner_controller.adapter_type}")

            self._instance_cache[miner_controller.id] = instance
            return instance
        except Exception as e:
            self.logger.error(
                f"Failed to initialize adapter '{miner_controller.name}' "
                f"(Type: {miner_controller.adapter_type}) using factory: {e}"
            )
            return None

    def _initialize_notifier_adapter(self, notifier: Notifier) -> Optional[NotificationAdapter]:
        """Initialize a notifier adapter."""
        # If the adapter has already been created, we use it.
        if notifier.id in self._instance_cache:
            self.logger.debug(
                f"Returning cached adapter instance " f"for notifier ID {notifier.id} (Type: {notifier.adapter_type})"
            )
            return self._instance_cache[notifier.id]

        # Retrieve the external service associated to the notifier
        if notifier.external_service_id:
            external_service = self.get_external_service(notifier.external_service_id)
            if not external_service:
                raise ValueError(
                    f"Unable to load external service {notifier.external_service_id} " f"for notifier {notifier.name}"
                )
        try:

            if notifier.adapter_type == NotificationAdapter.DUMMY.name:
                # --- Dummy Notifier ---
                instance = DummyNotifier()
            elif notifier.adapter_type == NotificationAdapter.TELEGRAM.name:
                # --- Telegram Notifier ---
                instance = TelegramNotifierFactory().create(
                    config=notifier.config,
                    logger=self.logger,
                    external_service=external_service,
                )
            else:
                raise ValueError(f"Unsupported notifier adapter type: {notifier.adapter_type}")

            self._instance_cache[notifier.id] = instance
            return instance
        except Exception as e:
            self.logger.error(
                f"Failed to initialize adapter '{notifier.name}' " f"(Type: {notifier.adapter_type}) using factory: {e}"
            )
            return None

    def _initialize_forecast_provider_adapter(
        self, energy_source: EnergySource, forecast_provider: ForecastProvider
    ) -> Optional[ForecastProviderPort]:
        """Initialize a forecast provider adapter."""
        # If the adapter has already been created, we use it.
        if forecast_provider.id in self._instance_cache:
            self.logger.debug(
                f"Returning cached adapter instance "
                f"for forecast provider ID {forecast_provider.id} "
                f"(Type: {forecast_provider.adapter_type})"
            )
            return self._instance_cache[forecast_provider.id]

        # Retrieve the external service associated to the forecast provider
        if forecast_provider.external_service_id:
            external_service = self.get_external_service(forecast_provider.external_service_id)
            if not external_service:
                raise ValueError(
                    f"Unable to load external service {forecast_provider.external_service_id} "
                    f"for forecast provider {forecast_provider.name}"
                )

        try:
            forecast_provider_adapter_factory: ForecastAdapterFactory = None

            if forecast_provider.adapter_type == ForecastProviderAdapter.DUMMY_SOLAR.name:
                # --- Dummy Forecast Provider ---
                if not energy_source:
                    raise ValueError("EnergySource is required " "for DummySolar forecast provider.")

                forecast_provider_adapter_factory = DummyForecastProviderFactory()

                # Set energy source as reference
                forecast_provider_adapter_factory.from_energy_source(energy_source)
            elif forecast_provider.adapter_type == ForecastProviderAdapter.HOME_ASSISTANT_API.name:
                # --- Home Assistant API Forecast Provider ---
                if not forecast_provider.config:
                    raise ValueError("ForecastProvider config is required " "for HomeAssistantAPI forecast provider.")

                forecast_provider_adapter_factory = HomeAssistantForecastProviderFactory()
            else:
                raise ValueError(f"Unsupported forecast provider adapter type: " f"{forecast_provider.adapter_type}")

            instance = forecast_provider_adapter_factory.create(
                config=forecast_provider.config,
                logger=self.logger,
                external_service=external_service,
            )

            self._instance_cache[forecast_provider.id] = instance
            return instance
        except Exception as e:
            self.logger.error(
                f"Failed to initialize adapter '{forecast_provider.name}' "
                f"(Type: {forecast_provider.adapter_type}) using factory: {e}"
            )
            return None

    def _initialize_home_forecast_provider_adapter(
        self, home_forecast_provider: HomeForecastProvider
    ) -> Optional[HomeForecastProviderPort]:
        """Initialize a home forecast provider adapter."""
        # If the adapter has already been created, we use it.
        if home_forecast_provider.id in self._instance_cache:
            self.logger.debug(
                f"Returning cached adapter instance "
                f"for home forecast provider ID {home_forecast_provider.id} "
                f"(Type: {home_forecast_provider.adapter_type})"
            )
            return self._instance_cache[home_forecast_provider.id]

        try:
            if home_forecast_provider.adapter_type == HomeForecastProviderAdapter.DUMMY.name:
                # --- Dummy Home Forecast Provider ---
                instance = DummyHomeForecastProvider(load_power_max=800)
            else:
                raise ValueError(
                    f"Unsupported home forecast provider adapter type: " f"{home_forecast_provider.adapter_type}"
                )

            self._instance_cache[home_forecast_provider.id] = instance
            return instance
        except Exception as e:
            self.logger.error(
                f"Failed to initialize adapter '{home_forecast_provider.name}' "
                f"(Type: {home_forecast_provider.adapter_type}) using factory: {e}"
            )
            return None

    def _initialize_mining_performace_tracker_adapter(
        self, tracker: MiningPerformanceTracker
    ) -> Optional[MiningPerformanceTrackerPort]:
        """Initialize a mining performace tracker adapter."""
        # If the adapter has already been created, we use it.
        if tracker.id in self._instance_cache:
            self.logger.debug(
                f"Returning cached adapter instance "
                f"for mining performace tracker ID {tracker.id} "
                f"(Type: {tracker.adapter_type})"
            )
            return self._instance_cache[tracker.id]

        # Retrieve the external service associated to the energy monitor
        if tracker.external_service_id:
            external_service = self.get_external_service(tracker.external_service_id)
            if not external_service:
                raise ValueError(
                    f"Unable to load external service {tracker.external_service_id} "
                    f"for mining performance tracker {tracker.name}"
                )

        try:
            instance: MiningPerformanceTrackerPort = None

            # No configuration is needed for the dummy tracker.
            # We instantiate it directly using DummyMiningPerformanceTracker.
            # In the future, if we may have other types of trackers
            # that require different initialization logic, we can use
            # a factory pattern similar to the other adapters.

            if tracker.adapter_type == MiningPerformanceTrackerAdapter.DUMMY.value:
                # --- Dummy Tracker ---

                instance = DummyMiningPerformanceTracker()
            else:
                raise ValueError(f"Unsupported mining performace tracker adapter type: " f"{tracker.adapter_type}")

            self._instance_cache[tracker.id] = instance
            return instance
        except Exception as e:
            self.logger.error(
                f"Failed to initialize adapter '{tracker.name}' " f"(Type: {tracker.adapter_type}) using factory: {e}"
            )
            return None

    def get_energy_monitor(self, energy_source: EnergySource) -> Optional[EnergyMonitorPort]:
        """Get an energy monitor adapter instance."""
        energy_monitor = self.energy_monitor_repo.get_by_id(energy_source.energy_monitor_id)
        if not energy_monitor:
            self.logger.error(
                f"EnergyMonitor ID {energy_source.energy_monitor_id} not found " f"or not an EnergyMonitor."
            )
            return None
        return self._initialize_energy_monitor_adapter(energy_source, energy_monitor)

    def get_miner_controller(self, miner: Miner) -> Optional[MinerControlPort]:
        """Get a miner controller adapter instance"""
        miner_controller = self.miner_controller_repo.get_by_id(miner.controller_id)
        if not miner_controller:
            self.logger.error(f"Miner Controller ID {miner.controller_id} not found " "or not a MinerController.")
            return None
        return self._initialize_miner_controller_adapter(miner, miner_controller)

    def get_all_notifiers(self) -> List[NotificationPort]:
        """Get all notifier adapter instances"""
        notifier_instances = []
        notifiers = self.notifier_repo.get_all()
        if not notifiers or not len(notifiers) > 0:
            self.logger.error("Notifiers not configured.")
            return None

        for notifier in notifiers:
            instance = self._initialize_notifier_adapter(notifier)
            if instance:
                notifier_instances.append(instance)
            else:
                self.logger.warning(f"Notifier ID {notifier.id} not found " "or not a Notification category.")
        return notifier_instances

    def get_notifier(self, notifier_id: EntityId) -> Optional[NotificationPort]:
        """Get a specific notifier adapter instance by ID."""
        notifier = self.notifier_repo.get_by_id(notifier_id)
        if not notifier:
            self.logger.error(f"Notifier ID {notifier_id} not found or not a Notifier.")
            return None
        return self._initialize_notifier_adapter(notifier)

    def get_notifiers(self, notifier_ids: List[EntityId]) -> List[NotificationPort]:
        """Get a list of specific notifier adapter instances by IDs."""
        notifier_instances = List[NotificationPort]()
        for notifier_id in notifier_ids:
            notifier = self.notifier_repo.get_by_id(notifier_id)
            if not notifier:
                self.logger.error(f"Notifier ID {notifier_id} not found or not a Notifier.")
                continue

            instance = self._initialize_notifier_adapter(notifier)
            if instance:
                notifier_instances.append(instance)
            else:
                self.logger.warning(f"Notifier ID {notifier.id} not found " "or not a Notification category.")
        return notifier_instances

    def get_forecast_provider(self, energy_source: EnergySource) -> Optional[ForecastProviderPort]:
        """Get a forecast provider adapter instance."""
        forecast_provider = self.forecast_provider_repo.get_by_id(energy_source.forecast_provider_id)
        if not forecast_provider:
            self.logger.error(
                f"Forecast Provider ID {energy_source.forecast_provider_id} not found or not a Forecast Provider."
            )
            return None
        return self._initialize_forecast_provider_adapter(energy_source, forecast_provider)

    def get_home_load_forecast_provider(
        self, home_forecast_provider_id: EntityId
    ) -> Optional[HomeForecastProviderPort]:
        """Get an home load forecast provider adapter instance."""
        home_forecast_provider = self.home_forecast_provider_repo.get_by_id(home_forecast_provider_id)
        if not home_forecast_provider:
            self.logger.error(
                f"Home Forecast Provider ID {home_forecast_provider_id} " f"not found or not a Home Forecast Provider."
            )
            return None
        return self._initialize_home_forecast_provider_adapter(home_forecast_provider)

    def get_mining_performace_tracker(self, tracker_id: EntityId) -> Optional[ForecastProviderPort]:
        """Get a mining performace tracker adapter instance."""
        tracker = self.mining_performance_tracker_repo.get_by_id(tracker_id)
        if not tracker:
            self.logger.error(
                f"Mining Performace Tracker ID {tracker_id} not found or not a Mining Performace Tracker."
            )
            return None
        return self._initialize_mining_performace_tracker_adapter(tracker)

    def get_external_service(self, external_service_id: EntityId) -> Optional[ExternalServicePort]:
        """Get a specific external service instance by ID."""
        external_service = self.external_service_repo.get_by_id(external_service_id)
        if not external_service:
            self.logger.error(f"External Service ID {external_service_id} not found or not an External Service.")
            return None
        return self._initialize_external_service(external_service)

    def get_rule_engine(self) -> Optional[RuleEngine]:
        """Creates a new Rule Engine instance."""
        try:
            # For now, we default to the 'custom' engine.
            # This could be driven by configuration in the future.
            factory = RuleEngineFactory()
            engine = factory.create(engine_type="custom", logger=self.logger)
            return engine
        except Exception as e:
            self.logger.error(f"Failed to create RuleEngine instance: {e}")
            return None

    def clear_all_adapters(self):
        """Clear adapter chache"""
        self.logger.info("Clearing all adapters.")
        self._instance_cache = {}  # Reset the cache

    def remove_adapter(self, entity_id: EntityId):
        """Remove a specific adapter from the cache."""
        if entity_id in self._instance_cache:
            del self._instance_cache[entity_id]
            self.logger.info(f"Removed adapter with ID {entity_id} from cache.")
        else:
            self.logger.warning(f"No adapter found with ID {entity_id} to remove.")

    def clear_all_services(self):
        """Clear external services chache"""
        self.logger.info("Clearing all external services.")
        self._service_cache = {}  # Reset the cache

    def remove_service(self, external_service_id: EntityId):
        """Remove a specific external seervice from the cache."""
        if external_service_id in self._service_cache:
            del self._service_cache[external_service_id]
            self.logger.info(f"Removed external service with ID {external_service_id} from cache.")
        else:
            self.logger.warning(f"No external service found with ID {external_service_id} to remove.")
