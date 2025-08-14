"""Terminal CLI infrastrusture adapter"""

import click

from edge_mining.adapters.domain.energy.cli.commands import energy_menu
from edge_mining.adapters.domain.forecast.cli.commands import forecast_menu
from edge_mining.adapters.domain.miner.cli.commands import miner_menu
from edge_mining.adapters.domain.notification.cli.commands import notifier_menu
from edge_mining.adapters.domain.optimization_unit.cli.commands import (
    optimization_unit_menu,
)
from edge_mining.adapters.domain.policy.cli.commands import policy_menu
from edge_mining.adapters.infrastructure.external_services.cli.commands import (
    external_services_menu,
)
from edge_mining.shared.infrastructure import Services
from edge_mining.shared.logging.port import LoggerPort


@click.group()
@click.pass_context
def cli(ctx: click.Context):
    """Edge Mining CLI"""

    if not isinstance(ctx.obj, dict) or not all(
        isinstance(ctx.obj.get(k), v)
        for k, v in {Services: Services, LoggerPort: LoggerPort}.items()
    ):
        print(
            "WARNING: ctx.obj does not contain expected pre-initialized dependencies."
        )
        click.echo(click.style("Welcome to the Edge Mining CLI!", fg="red", bold=True))


# @click.group()
# def cli():
#     """Edge Mining CLI"""
#     pass


# @optimization_unit.command("create")
# @click.argument("name")
# @click.option("--description", help="Description for the Optimization Unit")
# @click.option("--energy_source_id", help="ID of the energy source to use")
# @click.option("--target_miner_ids", help="Comma-separated list of target miner IDs")
# @click.option("--policy_id", help="ID of the policy to use")
# @click.option("--home_forecast_provider_id", help="ID of the home load forecast provider")
# @click.option("--performance_tracker_id", help="ID of the performance tracker")
# @click.option("--notifier_ids", help="Comma-separated list of notifier IDs")
# def create_optimization_unit(name, description, energy_source_id, target_miner_ids, policy_id, home_forecast_provider_id, performance_tracker_id, notifier_ids):
#     """Create a new optimization unit."""
#     if not _optimization_service:
#         click.echo("Error: Services not initialized.", err=True)
#         return

#     try:
#         target_miner_ids = target_miner_ids.split(",") if target_miner_ids else []
#         notifier_ids = notifier_ids.split(",") if notifier_ids else []

#         created = _configuration_service.create_optimization_unit(
#             name=name,
#             description=description,
#             energy_source_id=energy_source_id,
#             target_miner_ids=target_miner_ids,
#             policy_id=policy_id,
#             home_forecast_provider_id=home_forecast_provider_id,
#             performance_tracker_id=performance_tracker_id,
#             notifier_ids=notifier_ids
#         )
#         click.echo(f"Optimization Unit '{created.name}' created successfully.")
#     except Exception as e:
#         click.echo(f"Error creating optimization unit: {e}", err=True)

# @optimization_unit.command("list")
# def list_optimization_units():
#     """List all configured optimization units."""
#     if not _configuration_service:
#         click.echo("Error: Services not initialized.", err=True)
#         return

#     units = _configuration_service.list_optimization_units()
#     if not units:
#         click.echo("No optimization units configured.")
#         return

#     click.echo("Configured Optimization Units:")
#     for u in units:
#         click.echo(f"- ID: {u.id}, Name: {u.name}, Description: {u.description}, Target Miners: {', '.join(u.target_miner_ids)}")

# @cli.group()
# def miner():
#     """Manage Miners"""
#     pass

# @miner.command("add")
# @click.argument("name")
# @click.option("--hash_rate", help="Max HashRate of the miner", type=float, default=100.0)
# @click.option("--hash_rate_units", help="HashRate units (e.g. TH/s, GH/s)", default="TH/s")
# @click.option("--power_consumption", help="Max power consumption", type=float, default=3200.0)
# @click.option("--controller_id", help="Reference ID of miner controller", type=int, default=None)
# def add_miner(name, hash_rate, hash_rate_units, power_consumption, controller_id):
#     """Add a new miner to the system."""
#     if not _configuration_service:
#         click.echo("Error: Services not initialized.", err=True)
#         return
#     try:
#         added = _configuration_service.add_miner(
#             name=name,
#             hash_rate_max=hash_rate,
#             hash_rate_units=hash_rate_units,
#             power_consumption_max=power_consumption,
#             controller_id=controller_id
#         )
#         click.echo(f"Miner '{added.name}' ({added.id}) added successfully.")
#     except Exception as e:
#         click.echo(f"Error adding miner: {e}", err=True)

# @miner.command("list")
# def list_miners():
#     """List all configured miners."""
#     if not _configuration_service:
#         click.echo("Error: Services not initialized.", err=True)
#         return

#     miners = _configuration_service.list_miners()
#     if not miners:
#         click.echo("No miners configured.")
#         return

#     click.echo("Configured Miners:")
#     for m in miners:
#         click.echo(f"- ID: {m.id}, Name: {m.name}, Status: {m.status.name}, Power: {m.power_consumption}W")


# @miner.command("remove")
# @click.argument("miner_id")
# def remove_miner(miner_id):
#     """Remove a miner from the system."""
#     if not _config_service:
#        click.echo("Error: Services not initialized.", err=True)
#        return

#     try:
#        _config_service.remove_miner(miner_id=miner_id)
#        click.echo(f"Miner {miner_id} removed.")
#     except Exception as e:
#        click.echo(f"Error removing miner: {e}", err=True)


# @cli.group()
# def policy():
#     """Manage Optimization Policies"""
#     pass

# @policy.command("create")
# @click.argument("name")
# @click.argument("target_miner_ids")
# @click.option("--description", help="Description for the Policy")
# # @click.help_option(help=[
# #     "target_miner_ids: Use comma to separate multiple miner IDs"
# # ])
# def create_policy(name, description, target_miner_ids):
#     """Create a new optimization policy."""
#     if not _config_service:
#         click.echo("Error: Services not initialized.", err=True)
#         return
#     try:
#         target_miner_ids = list(target_miner_ids)  # Convert tuple to list

#         created = _config_service.create_policy(name=name, description=description, target_miner_ids=target_miner_ids)
#         click.echo(f"Optimization Policy '{created.name}' ({created.description}) on miners {created.target_miner_ids} created successfully.")
#     except Exception as e:
#         click.echo(f"Error adding miner: {e}", err=True)

# # TODO: Add commands for policy management (create, list, activate, add-rule)

# @cli.command("run-evaluation")
# def run_evaluation():
#     """Manually trigger one evaluation cycle."""
#     if not _orchestrator_service:
#         click.echo("Error: Services not initialized.", err=True)
#         return

#     click.echo("Manually running evaluation cycle...")
#     try:
#         _orchestrator_service.evaluate_and_control_miners()
#         click.echo("Evaluation cycle finished.")
#     except Exception as e:
#         click.echo(f"Error during evaluation: {e}", err=True)


# --- Main Menu Logic ---
@cli.command("interactive")
@click.pass_context
def interactive(ctx: click.Context):
    """Interactive main CLI menu for Edge Mining."""
    services: Services = ctx.obj[Services]
    logger: LoggerPort = ctx.obj[LoggerPort]

    click.echo(click.style("Welcome to the Edge Mining CLI!", fg="cyan", bold=True))
    click.echo("Select an option or use 'q' to quit.")

    sub_choice: str = ""

    while True:
        click.echo(click.style("\n--- Main Menu ---", fg="blue"))
        click.echo("1. Manage Energy")
        click.echo("2. Manage Forecast")
        click.echo("3. Manage Miners")
        click.echo("4. Manage Policies")
        click.echo("5. Manage Notifiers")
        click.echo("")
        click.echo("6. Manage Energy Optimization Units")
        click.echo("")
        click.echo("7. Manage External Services")
        click.echo("")
        click.echo("8. Run all optimization units)")
        click.echo("q. Close application")
        click.echo("--------------------------")

        sub_choice = ""
        choice: str = click.prompt("Choose an option", type=str)
        choice = choice.strip().lower()

        if choice == "1":
            sub_choice = energy_menu(
                configuration_service=services.configuration_service,
                logger=logger,
            )

            if sub_choice == "q":
                break
        elif choice == "2":
            sub_choice = forecast_menu(
                configuration_service=services.configuration_service,
                logger=logger,
            )

            if sub_choice == "q":
                break
        elif choice == "3":
            sub_choice = miner_menu(
                configuration_service=services.configuration_service,
                logger=logger,
            )

            if sub_choice == "q":
                break
        elif choice == "4":
            sub_choice = policy_menu(
                configuration_service=services.configuration_service,
                logger=logger,
            )

            if sub_choice == "q":
                break
        elif choice == "5":
            sub_choice = notifier_menu(
                configuration_service=services.configuration_service,
                logger=logger,
            )

            if sub_choice == "q":
                break
        elif choice == "6":
            sub_choice = optimization_unit_menu(
                configuration_service=services.configuration_service,
                logger=logger,
            )

            if sub_choice == "q":
                break
        elif choice == "7":
            sub_choice = external_services_menu(
                configuration_service=services.configuration_service,
                logger=logger,
            )

            if sub_choice == "q":
                break
        # elif choice == '3':
        #     handle_remove_miner()
        # elif choice == '4':
        #     handle_create_optimization_unit()
        # elif choice == '5':
        #     handle_list_optimization_units()
        # elif choice == '6':
        #     run_evaluation()
        elif choice == "q":
            break
        else:
            click.echo(click.style("Invalid option, please try again.", fg="red"))


# --- CLI main execution ---
def run_interactive_cli(services: Services, logger: LoggerPort):
    """
    Main function to launch the CLI interactive menu.
    """

    # Creates context object to pass services and logger
    context_data = {Services: services, LoggerPort: logger}

    # Creates a context object to pass services and logger using class names
    cli.main(obj=context_data)
