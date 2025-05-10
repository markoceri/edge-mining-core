"""Terminal CLI infrastrusture adapter"""

import click

from edge_mining.application.services.action_service import ActionService
from edge_mining.application.services.configuration_service import ConfigurationService
from edge_mining.application.services.mining_orchestrator import MiningOrchestratorService
from edge_mining.shared.logging.port import LoggerPort

# --- Simple way for Dependency Injection using global objects ---
_action_service: ActionService = None
_config_service: ConfigurationService = None
_orchestrator_service: MiningOrchestratorService = None
_logger: LoggerPort = None

def set_cli_services(
    action_service: ActionService,
    config_service: ConfigurationService,
    orchestrator_service: MiningOrchestratorService,
    logger: LoggerPort
):

    global _action_service, _config_service, _orchestrator_service, _logger

    _action_service = action_service
    _config_service = config_service
    _orchestrator_service = orchestrator_service
    _logger = logger
# ---

@click.group()
def cli():
    """Edge Mining CLI"""
    pass

@cli.group()
def miner():
    """Manage Miners"""
    pass

@miner.command("add")
@click.argument("name")
@click.option("--ip", help="IP Address of the miner")
def add_miner(name, ip):
    """Add a new miner to the system."""
    if not _config_service:
        click.echo("Error: Services not initialized.", err=True)
        return
    try:
        added = _config_service.add_miner(name=name, ip_address=ip)
        click.echo(f"Miner '{added.name}' ({added.id}) added successfully.")
    except Exception as e:
        click.echo(f"Error adding miner: {e}", err=True)

@miner.command("list")
def list_miners():
    """List all configured miners."""
    if not _config_service:
        click.echo("Error: Services not initialized.", err=True)
        return
    
    miners = _config_service.list_miners()
    if not miners:
        click.echo("No miners configured.")
        return
    
    click.echo("Configured Miners:")
    for m in miners:
        ip_str = f" (IP: {m.ip_address})" if m.ip_address else ""
        click.echo(f"- ID: {m.id}, Name: {m.name}, IP: {ip_str}, Status: {m.status.name}, Power: {m.power_consumption}W")


@miner.command("remove")
@click.argument("miner_id")
def remove_miner(miner_id):
    """Remove a miner from the system."""
    if not _config_service:
       click.echo("Error: Services not initialized.", err=True)
       return
   
    try:
       _config_service.remove_miner(miner_id=miner_id)
       click.echo(f"Miner {miner_id} removed.")
    except Exception as e:
       click.echo(f"Error removing miner: {e}", err=True)


@cli.group()
def policy():
    """Manage Optimization Policies"""
    pass
 
@policy.command("create")
@click.argument("name")
@click.argument("target_miner_ids")
@click.option("--description", help="Description for the Policy")
# @click.help_option(help=[
#     "target_miner_ids: Use comma to separate multiple miner IDs"
# ])
def create_policy(name, description, target_miner_ids):
    """Create a new optimization policy."""
    if not _config_service:
        click.echo("Error: Services not initialized.", err=True)
        return
    try:
        target_miner_ids = list(target_miner_ids)  # Convert tuple to list
        
        created = _config_service.create_policy(name=name, description=description, target_miner_ids=target_miner_ids)
        click.echo(f"Optimization Policy '{created.name}' ({created.description}) on miners {created.target_miner_ids} created successfully.")
    except Exception as e:
        click.echo(f"Error adding miner: {e}", err=True)

# TODO: Add commands for policy management (create, list, activate, add-rule)

@cli.command("run-evaluation")
def run_evaluation():
    """Manually trigger one evaluation cycle."""
    if not _orchestrator_service:
        click.echo("Error: Services not initialized.", err=True)
        return
    
    click.echo("Manually running evaluation cycle...")
    try:
        _orchestrator_service.evaluate_and_control_miners()
        click.echo("Evaluation cycle finished.")
    except Exception as e:
        click.echo(f"Error during evaluation: {e}", err=True)


# --- CLI main execution ---
def run_cli():
     # Here we would perform the dependency injection similar to __main__.py
     # but potentially without starting the scheduler, then call cli()
     # This part needs careful design based on how DI is handled.
     print("CLI entry point needs proper dependency injection setup.")
     # Example call after setting up services:
     # cli()
     pass

if __name__ == '__main__':
    # This allows running commands.py directly for basic testing
    # but without proper service injection.
    print("Running CLI directly (no services injected)")
    cli()