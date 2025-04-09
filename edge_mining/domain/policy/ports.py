"""Collection of Ports for the Energy Optimization domain of the Edge Mining application."""

from abc import ABC, abstractmethod
from typing import Optional, List

from edge_mining.domain.common import EntityId
from edge_mining.domain.policy.aggregate_roots import OptimizationPolicy

class OptimizationPolicyRepository(ABC):
    @abstractmethod
    def add(self, policy: OptimizationPolicy) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, policy_id: EntityId) -> Optional[OptimizationPolicy]:
        raise NotImplementedError

    @abstractmethod
    def get_active_policy(self) -> Optional[OptimizationPolicy]:
        """Gets the single currently active policy."""
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> List[OptimizationPolicy]:
        raise NotImplementedError

    @abstractmethod
    def update(self, policy: OptimizationPolicy) -> None:
        # Handles activating/deactivating policies as well
        raise NotImplementedError