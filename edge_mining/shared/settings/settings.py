"""Settings module for Edge Mining application."""

import os

from pydantic_settings import BaseSettings, SettingsConfigDict

# Using pydantic-settings for easy environment variable loading

# Helper to define a default path in the project directory
DEFAULT_SQLITE_DB_PATH = os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
), 'edgemining.db')
DEFAULT_YAML_DIR_PATH = os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
), 'optimization_policies')

class AppSettings(BaseSettings):
    """Settings for the Edge Mining application."""
    # Application settings
    log_level: str = "INFO"
    timezome: str = "Europe/Rome" # Default timezone

    # Adapters Configuration (select which ones to use)
    persistence_adapter: str = "sqlite" # Options: "in_memory", "sqlite", "yaml"
    policies_persistence_adapter: str = "yaml" # Options: "in_memory", "sqlite", "yaml"

    sqlite_db_file: str = DEFAULT_SQLITE_DB_PATH # SQLite file path
    yaml_policies_dir: str = DEFAULT_YAML_DIR_PATH # Directory for YAML policies

    # API Settings
    api_port: int = 8001

    # Scheduler settings
    scheduler_interval_seconds: int = 5 # Evaluate every 5 seconds

    # MQTT Adapter Settings (if energy_monitor_adapter=mqtt)
    # mqtt_broker_host: Optional[str] = "localhost"
    # mqtt_broker_port: int = 1883
    # mqtt_username: Optional[str] = None
    # mqtt_password: Optional[str] = None
    # mqtt_client_id: str = "edge_mining" # unique client ID
    # mqtt_topic_solar_production: Optional[str] = None # e.g., "home/energy/solar/power"
    # mqtt_topic_house_consumption: Optional[str] = None # e.g., "home/energy/consumption/power" (MUST exclude miner)
    # mqtt_topic_grid_power: Optional[str] = None # e.g., "home/energy/grid/power"
    # mqtt_topic_battery_soc: Optional[str] = None # e.g., "home/energy/battery/soc"
    # mqtt_topic_battery_power: Optional[str] = None # e.g., "home/energy/battery/power"
    # # --- Optional: Units (if topics report in kW instead of W) ---
    # mqtt_unit_solar_production: str = "W" # "W" or "kW"
    # mqtt_unit_house_consumption: str = "W" # "W" or "kW"
    # mqtt_unit_grid_power: str = "W" # "W" or "kW"
    # mqtt_unit_battery_power: str = "W" # "W" or "kW"
    # # --- Optional: Battery Capacity (if not available via a topic) ---
    # mqtt_battery_nominal_capacity_wh: Optional[float] = None # e.g., 10000.0
    # # --- Grid/Battery Power Convention ---
    # mqtt_grid_positive_export: bool = False
    # mqtt_battery_positive_charge: bool = True
    # # --- Data Staleness ---
    # mqtt_max_data_age_seconds: int = 300 # Max age in seconds before data is considered stale (5 min)

    model_config = SettingsConfigDict(
        env_file='.env',          # Load .env file if exists
        env_file_encoding='utf-8',
        extra='ignore'            # Ignore extra fields from env
    )
