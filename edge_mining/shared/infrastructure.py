"""Shared objects for infrastructure layer of Edge Mining application."""

from dataclasses import dataclass
from enum import Enum

from edge_mining.domain.energy.ports import EnergySourceRepository, EnergyMonitorRepository
from edge_mining.domain.miner.ports import MinerRepository, MinerControllerRepository
from edge_mining.domain.forecast.ports import ForecastProviderRepository
from edge_mining.domain.policy.ports import OptimizationPolicyRepository
from edge_mining.domain.home_load.ports import (
    HomeLoadsProfileRepository, HomeForecastProviderRepository
)
from edge_mining.domain.performance.ports import MiningPerformanceTrackerRepository
from edge_mining.domain.notification.ports import NotifierRepository
from edge_mining.domain.optimization_unit.ports import EnergyOptimizationUnitRepository
from edge_mining.shared.settings.ports import SettingsRepository
from edge_mining.shared.external_services.ports import ExternalServiceRepository

from edge_mining.application.interfaces import (
    AdapterServiceInterface, OptimizationServiceInterface,
    ActionServiceInterface, ConfigurationServiceInterface
)

class ApplicationMode(str, Enum):
    """Application run mode."""
    STANDARD = "standard"
    CLI = "cli"

@dataclass(frozen=True)
class PersistenceSettings():
    """Persistence reporitory adapters"""
    energy_source_repo: EnergySourceRepository
    energy_monitor_repo: EnergyMonitorRepository
    miner_repo: MinerRepository
    miner_controller_repo: MinerControllerRepository
    forecast_provider_repo: ForecastProviderRepository
    home_profile_repo: HomeLoadsProfileRepository
    home_forecast_provider_repo: HomeForecastProviderRepository
    policy_repo: OptimizationPolicyRepository
    mining_performance_tracker_repo: MiningPerformanceTrackerRepository
    optimization_unit_repo: EnergyOptimizationUnitRepository
    notifier_repo: NotifierRepository
    external_service_repo: ExternalServiceRepository
    settings_repo: SettingsRepository

@dataclass(frozen=True)
class Services():
    """Service layer adapters"""
    adapter_service: AdapterServiceInterface
    optimization_service: OptimizationServiceInterface
    miner_action_service: ActionServiceInterface
    configuration_service: ConfigurationServiceInterface
