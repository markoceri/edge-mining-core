"""Collection of Entities for the Energy Optimization domain of the Edge Mining application."""

from dataclasses import dataclass, field
from typing import Dict, Any

from edge_mining.domain.common import Entity, Watts, Percentage
from edge_mining.domain.policy.common import MiningDecision
from edge_mining.domain.policy.value_objects import DecisionalContext

@dataclass
class AutomationRule(Entity):
    """Entity for an automation rule."""
    name: str = ""
    conditions: Dict[str, Any] = field(
        default_factory=dict
    )  # e.g., {"battery_soc_gt": 80, "solar_forecast_gt": 1000}
    action: MiningDecision = field(
        default_factory=MiningDecision.STOP_MINING
    )  # e.g., MiningDecision.START_MINING

    def evaluate(
        self,
        decisional_context: DecisionalContext,
    ) -> bool:
        """Evaluates if the rule conditions are met."""
        # TODO: Implement complex rule evaluation logic based on 'conditions'
        print(f"Evaluating rule '{self.name}'...")

        # Example Simple Logic (Needs proper implementation)
        battery_soc_gt = self.conditions.get("battery_soc_gt")
        solar_forecast_gt = self.conditions.get("solar_forecast_gt")
        battery_soc_lt = self.conditions.get("battery_soc_lt") # For stopping

        if battery_soc_gt is not None and decisional_context.energy_state.battery:
            if decisional_context.energy_state.battery.state_of_charge <= Percentage(battery_soc_gt):
                return False # Condition not met

        if solar_forecast_gt is not None and decisional_context.forecast:
            # Assuming forecast.predicted_power is a list or similar
            # This needs refinement based on ForecastData structure
            if not any(
                p > Watts(solar_forecast_gt) for p in decisional_context.forecast.predicted_power.values()
            ):  # Simplistic check
                return False  # Condition not met

        if battery_soc_lt is not None and decisional_context.energy_state.battery:
            if decisional_context.energy_state.battery.state_of_charge >= Percentage(battery_soc_lt):
                return False # Condition not met (use for STOP rules)

        print(f"Rule '{self.name}' conditions met.")
        return True
