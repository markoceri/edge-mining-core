"""Home Assistant API adapter (Implementation of Port) for the energy provisioning of Edge Mining Application using the Home Assistant API"""

"""
The REST API for Home Assistant has been superseded by the websocket API.
I use it only for simplicity, in the future I plan to switch to websocket API

https://github.com/home-assistant/architecture/discussions/1074#discussioncomment-9196867

and

https://github.com/home-assistant/developers.home-assistant/pull/2150
"""
import logging
from typing import Optional, Tuple
from datetime import datetime
import math # For isnan


try:
    from homeassistant_api import Client
except ImportError:
    raise ImportError("Please install 'homeassistant_api' (`pip install homeassistant_api`) to use the Home Assistant energy monitor.")


from edge_mining.domain.energy.ports import EnergyMonitorPort
from edge_mining.domain.common import Watts, Percentage, WattHours, Timestamp
from edge_mining.domain.energy.value_objects import EnergyStateSnapshot, BatteryState

logger = logging.getLogger(__name__)

class HomeAssistantEnergyMonitor(EnergyMonitorPort):
    """
    Fetches energy data from a Home Assistant instance via its REST API.

    Requires careful configuration of entity IDs in the .env file.
    Make sure the House Consumption entity EXCLUDES the miner's consumption,
    possibly using a template sensor in Home Assistant.
    """
    def __init__(
        self,
        api_url: str,
        token: str,
        entity_solar: Optional[str],
        entity_consumption: Optional[str],
        entity_grid: Optional[str],
        entity_battery_soc: Optional[str],
        entity_battery_power: Optional[str],
        unit_solar: str = "W",
        unit_consumption: str = "W",
        unit_grid: str = "W",
        unit_battery_power: str = "W",
        battery_capacity_wh: Optional[float] = None,
        grid_positive_export: bool = False, # True if positive grid = export
        battery_positive_charge: bool = True # True if positive battery = charge
    ):
        if not api_url or not token:
            raise ValueError("Home Assistant URL and Token are required.")

        self.entity_solar = entity_solar
        self.entity_consumption = entity_consumption
        self.entity_grid = entity_grid
        self.entity_battery_soc = entity_battery_soc
        self.entity_battery_power = entity_battery_power
        self.unit_solar = unit_solar.lower()
        self.unit_consumption = unit_consumption.lower()
        self.unit_grid = unit_grid.lower()
        self.unit_battery_power = unit_battery_power.lower()
        self.battery_capacity = WattHours(battery_capacity_wh) if battery_capacity_wh else None
        self.grid_positive_export = grid_positive_export
        self.battery_positive_charge = battery_positive_charge

        logger.info(f"Initializing HomeAssistantEnergyMonitor for {api_url}")
        logger.debug(f"Entities Configured: Solar='{entity_solar}', Consumption='{entity_consumption}', "
                     f"Grid='{entity_grid}', BatterySOC='{entity_battery_soc}', BatteryPower='{entity_battery_power}'")
        logger.debug(f"Units: Solar='{unit_solar}', Consumption='{unit_consumption}', "
                     f"Grid='{unit_grid}', BatteryPower='{unit_battery_power}'")
        logger.debug(f"Conventions: Grid Positive Export='{grid_positive_export}', "
                     f"Battery Positive Charge='{battery_positive_charge}'")
        if self.battery_capacity:
             logger.debug(f"Static Battery Capacity: {self.battery_capacity} Wh")


        # Initialize Home Assistant client
        try:
            self.client = Client(api_url, token)
            # Test connection during initialization (optional but recommended)
            self.client.get_config()
            logger.info("Successfully connected to Home Assistant API.")
        except Exception as e:
            logger.error(f"An unexpected error occurred connecting to Home Assistant: {e}")
            raise ConnectionError(f"Unexpected error connecting to Home Assistant: {e}") from e


    def _get_entity_state(self, entity_id: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """Safely retrieves the state and unit of an entity."""
        if not entity_id:
            return None, None
        try:
            entity = self.client.get_entity(entity_id=entity_id)
            # Check if state is unavailable or unknown
            state = entity.state.state # The actual value as a string
            if state is None or state.lower() in ["unavailable", "unknown"]:
                logger.warning(f"Home Assistant entity '{entity_id}' is unavailable or unknown.")
                return None, None

            unit = entity.state.attributes.get("unit_of_measurement")
            logger.debug(f"Fetched HA entity '{entity_id}': State='{state}', Unit='{unit}'")
            return state, unit
        except Exception as e:
            logger.error(f"Unexpected error getting Home Assistant entity '{entity_id}': {e}")
            return None, None


    def _parse_power(self, state: Optional[str], configured_unit: str, entity_id_for_log: str) -> Optional[Watts]:
        """Parses state string to Watts, handling units (W/kW) and errors."""
        if state is None:
            return None
        try:
            value = float(state)
            if math.isnan(value):
                logger.warning(f"Parsed NaN value for entity '{entity_id_for_log}', state='{state}'. Treating as missing.")
                return None
            if configured_unit == "kw":
                value *= 1000 # Convert kW to W
            elif configured_unit != "w":
                 logger.warning(f"Unsupported unit '{configured_unit}' configured for entity '{entity_id_for_log}'. Assuming Watts.")

            return Watts(value)
        except (ValueError, TypeError) as e:
            logger.error(f"Could not parse power value for entity '{entity_id_for_log}' from state='{state}': {e}")
            return None


    def _parse_percentage(self, state: Optional[str], entity_id_for_log: str) -> Optional[Percentage]:
        """Parses state string to Percentage, handling errors."""
        if state is None:
            return None
        try:
            value = float(state)
            if math.isnan(value):
                logger.warning(f"Parsed NaN value for entity '{entity_id_for_log}', state='{state}'. Treating as missing.")
                return None
            return Percentage(max(0.0, min(100.0, value))) # Clamp between 0 and 100
        except (ValueError, TypeError) as e:
            logger.error(f"Could not parse percentage value for entity '{entity_id_for_log}' from state='{state}': {e}")
            return None


    def get_current_energy_state(self) -> Optional[EnergyStateSnapshot]:
        logger.debug("Fetching current energy state from Home Assistant...")
        now = Timestamp(datetime.now())
        has_critical_error = False

        # Fetch states from Home Assistant
        state_solar, _ = self._get_entity_state(self.entity_solar)
        state_consumption, _ = self._get_entity_state(self.entity_consumption)
        state_grid, _ = self._get_entity_state(self.entity_grid)
        state_battery_soc, _ = self._get_entity_state(self.entity_battery_soc)
        state_battery_power, _ = self._get_entity_state(self.entity_battery_power)

        # Parse values, converting units and handling errors
        production_watts = self._parse_power(state_solar, self.unit_solar, self.entity_solar or "N/A")
        consumption_watts = self._parse_power(state_consumption, self.unit_consumption, self.entity_consumption or "N/A")
        grid_watts_raw = self._parse_power(state_grid, self.unit_grid, self.entity_grid or "N/A")
        battery_soc = self._parse_percentage(state_battery_soc, self.entity_battery_soc or "N/A")
        battery_power_raw = self._parse_power(state_battery_power, self.unit_battery_power, self.entity_battery_power or "N/A")

        # --- Apply Conventions ---
        # Grid: We want positive for IMPORTING, negative for EXPORTING
        if grid_watts_raw is not None:
            grid_watts = -grid_watts_raw if self.grid_positive_export else grid_watts_raw
        else:
            grid_watts = None
            if self.entity_grid: has_critical_error = True # Grid is usually important

        # Battery: We want positive for CHARGING, negative for DISCHARGING
        if battery_power_raw is not None:
            battery_power = battery_power_raw if self.battery_positive_charge else -battery_power_raw
        else:
            battery_power = None
            # Only critical if battery SOC is also configured
            if self.entity_battery_soc and self.entity_battery_power: has_critical_error = True

        # Check if essential values are missing
        if production_watts is None and self.entity_solar:
             logger.error(f"Missing critical value: Solar Production (Entity: {self.entity_solar})")
             has_critical_error = True
        if consumption_watts is None and self.entity_consumption:
             logger.error(f"Missing critical value: House Consumption (Entity: {self.entity_consumption})")
             has_critical_error = True

        if has_critical_error:
            logger.error("Failed to retrieve one or more critical energy values from Home Assistant. Cannot create snapshot.")
            return None

        # Fill defaults if entities weren't configured
        production_watts = production_watts if production_watts is not None else Watts(0.0)
        consumption_watts = consumption_watts if consumption_watts is not None else Watts(0.0)
        grid_watts = grid_watts if grid_watts is not None else Watts(0.0) # Assume 0 if no grid sensor


        # Construct BatteryState if relevant entities are available
        battery_state: Optional[BatteryState] = None
        if battery_soc is not None and battery_power is not None and self.battery_capacity is not None:
            battery_state = BatteryState(
                state_of_charge=battery_soc,
                nominal_capacity=self.battery_capacity, # Use configured capacity
                current_power=battery_power,
                timestamp=now
            )
        elif self.entity_battery_soc: # Log if configured but data missing
            logger.warning("Battery SOC entity configured, but could not create full BatteryState "
                           "(missing power or static capacity setting?).")


        snapshot = EnergyStateSnapshot(
            production=production_watts,
            consumption=consumption_watts,
            battery=battery_state,
            grid_power=grid_watts,
            timestamp=now
        )

        logger.info(f"HA Monitor: State fetched: Prod={snapshot.production:.0f}W, "
                    f"Cons={snapshot.consumption:.0f}W, Grid={snapshot.grid_power:.0f}W, "
                    f"SOC={snapshot.battery.state_of_charge if snapshot.battery else 'N/A'}%, "
                    f"BattPwr={snapshot.battery.current_power if snapshot.battery else 'N/A'}W")
        return snapshot