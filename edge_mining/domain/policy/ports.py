"""Collection of Ports for the Energy Optimization domain of the Edge Mining application."""

from abc import ABC, abstractmethod
from typing import Optional, List

from edge_mining.domain.common import EntityId
from edge_mining.domain.policy.aggregate_roots import OptimizationPolicy
from edge_mining.domain.policy.entities import AutomationRule
from edge_mining.domain.policy.value_objects import DecisionalContext

class OptimizationPolicyRepository(ABC):
    """Port for the Optimization Policy Repository."""
    @abstractmethod
    def add(self, policy: OptimizationPolicy) -> None:
        """Adds a policy to the repository."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, policy_id: EntityId) -> Optional[OptimizationPolicy]:
        """Gets a policy by its ID."""
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> List[OptimizationPolicy]:
        """Gets all policies from the repository."""
        raise NotImplementedError

    @abstractmethod
    def update(self, policy: OptimizationPolicy) -> None:
        """Updates a policy in the repository."""
        # Handles activating/deactivating policies as well
        raise NotImplementedError

    @abstractmethod
    def remove(self, policy_id: EntityId) -> None:
        """Removes a policy by its ID."""
        raise NotImplementedError

class RuleEngine(ABC):
    """Port for rule engine."""
    @abstractmethod
    def load_rules(self, rules: List[AutomationRule]) -> None:
        """
        Loads rules. This method should be called before evaluating any rules.
        """
        raise NotImplementedError

    @abstractmethod
    def evaluate(self, context: DecisionalContext) -> bool:
        """
        Evaluates rules based on the given context and returns True if any rule matches.
        If no rules match, returns False.
        This is the core decision-making logic of the rule engine.
        """
        raise NotImplementedError
