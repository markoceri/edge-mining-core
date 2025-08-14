"""Utility functions for CLI commands."""

from functools import wraps

import click

from edge_mining.application.services.adapter_service import AdapterService
from edge_mining.application.services.configuration_service import ConfigurationService
from edge_mining.application.services.miner_action_service import MinerActionService
from edge_mining.application.services.optimization_service import OptimizationService
from edge_mining.shared.infrastructure import Services
from edge_mining.shared.logging.port import LoggerPort

global _cli_adapter_service, _cli_optimization_service, _cli_miner_action_service, _cli_configuration_service, _cli_logger

_cli_adapter_service: AdapterService = None
_cli_optimization_service: OptimizationService = None
_cli_miner_action_service: MinerActionService = None
_cli_configuration_service: ConfigurationService = None
_cli_logger: LoggerPort = None


# --- Decorator to check if services are initialized ---
def requires_services(func):
    """Check if required services are initialized before executing a command."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        global _cli_adapter_service, _cli_optimization_service, _cli_miner_action_service, _cli_configuration_service, _cli_logger

        # Check if all required services are initialized
        if not all(
            [
                _cli_adapter_service,
                _cli_optimization_service,
                _cli_miner_action_service,
                _cli_configuration_service,
                _cli_logger,
            ]
        ):
            click.echo(
                click.style("Error: Services not initialized.", fg="red"),
                err=True,
            )
            click.pause("Press any key to return to the menu...")
            return
        return func(*args, **kwargs)

    return wrapper


# --- Simple way for Dependency Injection using global objects ---
def set_cli_services(services: Services, logger: LoggerPort):
    """Set the services for the CLI commands."""

    _cli_adapter_service = (services.adapter_service,)
    _cli_optimization_service = (services.optimization_service,)
    _cli_miner_action_service = (services.miner_action_service,)
    _cli_configuration_service = services.configuration_service
    _cli_logger = logger
