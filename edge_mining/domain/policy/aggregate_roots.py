"""Collection of Aggregate Roots for the Energy Optimization domain of the Edge Mining application."""

from dataclasses import dataclass, field
from typing import List, Optional

from edge_mining.domain.common import AggregateRoot
from edge_mining.domain.policy.common import MiningDecision
from edge_mining.domain.policy.entities import AutomationRule
from edge_mining.domain.policy.value_objects import DecisionalContext
from edge_mining.domain.miner.common import MinerStatus

@dataclass
class OptimizationPolicy(AggregateRoot):
    """Aggregate Root for the Optimization Policy."""
    name: str = ""
    description: Optional[str] = None

    start_rules: List[AutomationRule] = field(default_factory=list)
    stop_rules: List[AutomationRule] = field(default_factory=list)

    def decide_next_action(
        self,
        decisional_context: DecisionalContext,
    ) -> MiningDecision:
        """
        Applies the policy rules to determine the next action.
        This is the core decision-making logic.
        """
        print(
            f"Policy '{self.name}': Evaluating state for miner status {decisional_context.miner.status.name}"
        )

        # Logic:
        # 1. If miner is OFF, check START rules. If any match -> START_MINING
        # 2. If miner is ON, check STOP rules. If any match -> STOP_MINING
        # 3. Otherwise -> MAINTAIN_STATE

        # This is the location where the magic happens!

        if decisional_context.miner.status in [MinerStatus.OFF, MinerStatus.ERROR, MinerStatus.UNKNOWN]:
            for rule in self.start_rules:
                if rule.evaluate(decisional_context):
                    print(f"Policy '{self.name}': Start condition met by rule '{rule.name}'.")
                    return MiningDecision.START_MINING
            return MiningDecision.MAINTAIN_STATE # Stay off if no start rule matches

        elif decisional_context.miner.status is MinerStatus.ON:
            for rule in self.stop_rules:
                if rule.evaluate(decisional_context):
                    print(f"Policy '{self.name}': Stop condition met by rule '{rule.name}'.")
                    return MiningDecision.STOP_MINING
            return MiningDecision.MAINTAIN_STATE # Stay on if no stop rule matches

        # For STARTING/STOPPING states, usually maintain state until confirmed ON/OFF
        return MiningDecision.MAINTAIN_STATE
