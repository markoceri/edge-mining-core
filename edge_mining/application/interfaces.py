"""Edge Mining Application Interfaces Module"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from edge_mining.domain.common import EntityId, Watts
from edge_mining.domain.energy.entities import EnergySource
from edge_mining.domain.energy.ports import EnergyMonitorPort
from edge_mining.domain.forecast.ports import ForecastProviderPort
from edge_mining.domain.miner.entities import Miner
from edge_mining.domain.miner.ports import MinerControlPort
from edge_mining.domain.miner.value_objects import HashRate
from edge_mining.domain.notification.ports import NotificationPort
from edge_mining.domain.policy.aggregate_roots import (
    AutomationRule,
    MiningDecision,
    OptimizationPolicy,
)
from edge_mining.domain.policy.common import RuleType
from edge_mining.domain.policy.services import RuleEngine
from edge_mining.domain.policy.value_objects import Sun
from edge_mining.shared.external_services.ports import ExternalServicePort


class AdapterServiceInterface(ABC):
    """Base interface for all adapter services in the Edge Mining application."""

    @abstractmethod
    def get_energy_monitor(
        self, energy_source: EnergySource
    ) -> Optional[EnergyMonitorPort]:
        """Get an energy monitor adapter instance."""
        pass

    @abstractmethod
    def get_miner_controller(self, miner: Miner) -> Optional[MinerControlPort]:
        """Get a miner controller adapter instance"""
        pass

    @abstractmethod
    def get_all_notifiers(self) -> List[NotificationPort]:
        """Get all notifier adapter instances"""
        pass

    @abstractmethod
    def get_notifier(self, notifier_id: EntityId) -> Optional[NotificationPort]:
        """Get a specific notifier adapter instance by ID."""
        pass

    @abstractmethod
    def get_notifiers(self, notifier_ids: List[EntityId]) -> List[NotificationPort]:
        """Get a list of specific notifiers adapter instance by IDs."""
        pass

    @abstractmethod
    def get_forecast_provider(
        self, energy_source: EnergySource
    ) -> Optional[ForecastProviderPort]:
        """Get a forecast provider adapter instance."""
        pass

    @abstractmethod
    def get_home_load_forecast_provider(
        self, home_forecast_provider_id: EntityId
    ) -> Optional[ForecastProviderPort]:
        """Get an home load forecast provider adapter instance."""
        pass

    @abstractmethod
    def get_mining_performace_tracker(
        self, tracker_id: EntityId
    ) -> Optional[ForecastProviderPort]:
        """Get a mining performace tracker adapter instance."""
        pass

    @abstractmethod
    def get_external_service(
        self, external_service_id: EntityId
    ) -> Optional[ExternalServicePort]:
        """Get a specific external service instance by ID."""
        pass

    @abstractmethod
    def get_rule_engine(self) -> Optional[RuleEngine]:
        """Get the rule engine instance."""
        pass

    @abstractmethod
    def clear_all_adapters(self):
        """Clear adapter chache"""
        pass

    @abstractmethod
    def remove_adapter(self, entity_id: EntityId):
        """Remove a specific adapter from the cache."""
        pass

    @abstractmethod
    def clear_all_services(self):
        """Clear external services chache"""
        pass

    @abstractmethod
    def remove_service(self, external_service_id: EntityId):
        """Remove a specific external seervice from the cache."""
        pass


class OptimizationServiceInterface(ABC):
    """Base interface for optimization services in the Edge Mining application."""

    @abstractmethod
    async def run_all_enabled_units(self):
        """Run the optimization process for all enabled units."""
        pass


class ActionServiceInterface(ABC):
    """Base interface for action services in the Edge Mining application."""

    @abstractmethod
    async def start_miner(
        self, miner_id: EntityId, notifiers: List[NotificationPort]
    ) -> bool:
        """Start a specific miner."""
        pass

    @abstractmethod
    async def stop_miner(
        self, miner_id: EntityId, notifiers: List[NotificationPort]
    ) -> bool:
        """Stop a specific miner."""
        pass

    @abstractmethod
    def get_miner_consumption(self, miner_id: EntityId) -> Optional[Watts]:
        """Gets the current power consumption of the specified miner."""

    @abstractmethod
    def get_miner_hashrate(self, miner_id: EntityId) -> Optional[HashRate]:
        """Gets the current hash rate of the specified miner."""


class ConfigurationServiceInterface(ABC):
    """Base interface for configuration services in the Edge Mining application."""

    @abstractmethod
    def add_miner(
        self,
        name: str,
        ip_address: Optional[str] = None,
        hash_rate_max: Optional[HashRate] = None,
        power_consumption_max: Optional[Watts] = None,
        active: Optional[bool] = True,
    ) -> Miner:
        """Add a miner to the system."""
        pass

    @abstractmethod
    def get_miner(self, miner_id: EntityId) -> Optional[Miner]:
        """Get a miner by its ID."""
        pass

    @abstractmethod
    def list_miners(self) -> List[Miner]:
        """List all miners in the system."""
        pass

    @abstractmethod
    def remove_miner(self, miner_id: EntityId) -> Miner:
        """Remove a miner from the system."""
        pass

    @abstractmethod
    def update_miner(
        self,
        miner_id: EntityId,
        name: str,
        ip_address: Optional[str] = None,
        hash_rate_max: Optional[HashRate] = None,
        power_consumption_max: Optional[Watts] = None,
        active: Optional[bool] = True,
    ) -> Miner:
        """Update a miner in the system."""
        pass

    @abstractmethod
    def activate_miner(self, miner_id: EntityId) -> Miner:
        """Activate a miner in the system."""
        pass

    @abstractmethod
    def deactivate_miner(self, miner_id: EntityId) -> Miner:
        """Deactivate a miner in the system."""
        pass

    # --- Policy Management ---
    @abstractmethod
    def create_policy(
        self,
        name: str,
        description: str = "",
        target_miner_ids: Optional[List[EntityId]] = None,
    ) -> OptimizationPolicy:
        """Create a new policy."""
        pass

    @abstractmethod
    def get_policy(self, policy_id: EntityId) -> Optional[OptimizationPolicy]:
        """Get a policy by its ID."""
        pass

    @abstractmethod
    def list_policies(self) -> List[OptimizationPolicy]:
        """List all policies in the system."""
        pass

    @abstractmethod
    def add_rule_to_policy(
        self,
        policy_id: EntityId,
        rule_type: RuleType,
        name: str,
        conditions: dict,
        action: MiningDecision,
    ) -> AutomationRule:
        """Add a rule to a policy."""
        pass

    @abstractmethod
    def get_policy_rules(
        self, policy_id: EntityId, rule_type: RuleType
    ) -> List[AutomationRule]:
        """Get all rules of a policy."""
        pass

    @abstractmethod
    def get_policy_rule(
        self, policy_id: EntityId, rule_id: EntityId
    ) -> Optional[AutomationRule]:
        """Get a rule by its ID."""
        pass

    @abstractmethod
    def update_policy_rule(
        self,
        policy_id: EntityId,
        rule_id: EntityId,
        name: str,
        conditions: dict,
        action: MiningDecision,
    ) -> AutomationRule:
        """Update a rule in a policy."""
        pass

    @abstractmethod
    def delete_policy_rule(
        self, policy_id: EntityId, rule_id: EntityId
    ) -> AutomationRule:
        """Delete a rule from a policy."""
        pass

    @abstractmethod
    def set_active_policy(self, policy_id: EntityId) -> None:
        """Set a policy as active."""
        pass

    @abstractmethod
    def get_active_policy(self) -> Optional[OptimizationPolicy]:
        """Get the active policy."""
        pass

    @abstractmethod
    def delete_policy(self, policy_id: EntityId) -> Optional[OptimizationPolicy]:
        """Delete a policy from the system."""
        pass

    # --- Settings Management ---
    @abstractmethod
    def get_all_settings(self) -> dict:
        """Get all settings."""
        pass

    @abstractmethod
    def update_setting(self, key: str, value: any) -> None:
        """Update a setting."""
        pass


class SunFactoryInterface(ABC):
    """Base interface for Sun factories in the Edge Mining application."""

    @abstractmethod
    def create_sun_for_date(self, for_date: datetime = datetime.now) -> Sun:
        """Create a Sun object for a specific date."""
        pass
