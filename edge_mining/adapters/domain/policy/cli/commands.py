"""CLI commands for the policy domain."""

from typing import Optional, List, Dict, Any

import click

from edge_mining.domain.common import EntityId
from edge_mining.domain.policy.common import MiningDecision, RuleType
from edge_mining.domain.policy.aggregate_roots import OptimizationPolicy
from edge_mining.domain.policy.exceptions import PolicyError, PolicyNotFoundError
from edge_mining.domain.miner.common import MinerStatus

from edge_mining.application.services.configuration_service import ConfigurationService
from edge_mining.shared.logging.port import LoggerPort


def select_mining_decision() -> Optional[MiningDecision]:
    """Select a mining decision from the available options."""
    click.echo("Select a Mining Decision:")
    for idx, decision in enumerate(MiningDecision):
        color = "green" if decision == MiningDecision.START_MINING else ("red" if decision == MiningDecision.STOP_MINING else "yellow")
        click.echo(f"{idx}. {click.style(decision.value, fg=color)}")

    click.echo("")
    choice: str = click.prompt("Choose a mining decision", type=str)
    choice = choice.strip().lower()

    if not choice.isdigit() or int(choice) < 0 or int(choice) >= len(MiningDecision):
        click.echo(click.style("Invalid choice. Please try again.", fg="red"))
        return None

    decision_values = [decision.value for decision in MiningDecision]
    selected_decision = MiningDecision(decision_values[int(choice)])
    return selected_decision


def select_rule_type() -> Optional[RuleType]:
    """Select a rule type from the available options."""
    click.echo("Select a Rule Type:")
    for idx, rule_type in enumerate(RuleType):
        color = "green" if rule_type == RuleType.START else "red"
        click.echo(f"{idx}. {click.style(rule_type.value, fg=color)}")

    click.echo("")
    choice: str = click.prompt("Choose a rule type", type=str)
    choice = choice.strip().lower()

    if not choice.isdigit() or int(choice) < 0 or int(choice) >= len(RuleType):
        click.echo(click.style("Invalid choice. Please try again.", fg="red"))
        return None

    rule_type_values = [rule_type.value for rule_type in RuleType]
    selected_rule_type = RuleType(rule_type_values[int(choice)])
    return selected_rule_type


def create_rule_conditions() -> Dict[str, Any]:
    """Create rule conditions interactively."""
    conditions = {}
    
    click.echo(click.style("\n--- Define Rule Conditions ---", fg="yellow"))
    click.echo("Available condition types:")
    click.echo("1. Battery SOC greater than (battery_soc_gt)")
    click.echo("2. Battery SOC less than (battery_soc_lt)")
    click.echo("3. Solar forecast greater than (solar_forecast_gt)")
    click.echo("4. Solar forecast less than (solar_forecast_lt)")
    click.echo("5. Done (finish adding conditions)")

    while True:
        choice = click.prompt("\nSelect condition type (1-5)", type=int, default=5)
        
        if choice == 5:
            break
        elif choice == 1:
            value = click.prompt("Enter battery SOC percentage (0-100)", type=float)
            conditions["battery_soc_gt"] = value
        elif choice == 2:
            value = click.prompt("Enter battery SOC percentage (0-100)", type=float)
            conditions["battery_soc_lt"] = value
        elif choice == 3:
            value = click.prompt("Enter solar forecast power (W)", type=int)
            conditions["solar_forecast_gt"] = value
        elif choice == 4:
            value = click.prompt("Enter solar forecast power (W)", type=int)
            conditions["solar_forecast_lt"] = value
        else:
            click.echo(click.style("Invalid choice. Please try again.", fg="red"))
    
    return conditions


def handle_add_optimization_policy(
    configuration_service: ConfigurationService, logger: LoggerPort
) -> None:
    """Menu to add a new optimization policy."""
    click.echo(click.style("\n--- Add Optimization Policy ---", fg="yellow"))

    name: str = click.prompt("Name of the optimization policy", type=str)
    description: str = click.prompt("Description (optional)", type=str, default="")

    try:
        new_policy = configuration_service.create_policy(
            name=name,
            description=description
        )

        if not new_policy:
            click.echo(click.style("Failed to create optimization policy.", fg="red"))
            raise PolicyError("Policy creation failed")

        click.echo(click.style(f"Optimization policy '{name}' created successfully!", fg="green"))

        click.echo()
        click.echo(
            click.style(f"{RuleType.START.name}", fg="green") +
            " rules are evaluated when the miner is in " + 
            click.style(f"{MinerStatus.OFF.name}", fg="red") +
            " status"
        )
        click.echo(
            click.style(f"{RuleType.STOP.name}", fg="red") +
            " rules are evaluated when the miner is in " + 
            click.style(f"{MinerStatus.ON.name}", fg="green") +
            " status"
        )
        click.echo()

        conditions: Dict[str, Any] = dict()

        # Now add rules to the policy if requested
        if click.confirm("Add start rules?", default=True):
            click.echo("\nAdding START rules:")
            while True:
                rule_name = click.prompt("Start rule name", type=str)
                conditions = create_rule_conditions()
                
                if conditions:
                    configuration_service.add_rule_to_policy(
                        policy_id=new_policy.id,
                        rule_type=RuleType.START,
                        name=rule_name,
                        conditions=conditions,
                        action=MiningDecision.START_MINING
                    )
                    click.echo(click.style(f"Start rule '{rule_name}' added!", fg="green"))
                    
                    if not click.confirm("Add another start rule?", default=False):
                        break
                else:
                    break

        # Add stop rules
        if click.confirm("Add stop rules?", default=True):
            click.echo("\nAdding STOP rules:")
            while True:
                rule_name = click.prompt("Stop rule name", type=str)
                conditions = create_rule_conditions()
                
                if conditions:
                    configuration_service.add_rule_to_policy(
                        policy_id=new_policy.id,
                        rule_type=RuleType.STOP,
                        name=rule_name,
                        conditions=conditions,
                        action=MiningDecision.STOP_MINING
                    )
                    click.echo(click.style(f"Stop rule '{rule_name}' added!", fg="green"))
                    
                    if not click.confirm("Add another stop rule?", default=False):
                        break
                else:
                    break

        if conditions.keys():
            click.echo(click.style("Rules added successfully to Optimization policy '{name}'", fg="green"))
        
    except (PolicyError, PolicyNotFoundError) as e:
        click.echo(click.style(f"Policy error: {str(e)}", fg="red"))
        logger.error(f"Policy error adding optimization policy: {str(e)}")
    except Exception as e:  # Catch-all for unexpected errors
        click.echo(click.style(f"Error adding optimization policy: {str(e)}", fg="red"))
        logger.error(f"Error adding optimization policy: {str(e)}")
    
    click.pause("Press any key to return to the menu...")


def handle_list_optimization_policies(
    configuration_service: ConfigurationService
) -> None:
    """List all optimization policies."""
    click.echo(click.style("\n--- List Optimization Policies ---", fg="yellow"))

    policies: List[OptimizationPolicy] = configuration_service.list_policies()
    if not policies:
        click.echo(click.style("No optimization policies found.", fg="red"))
    else:
        for idx, policy in enumerate(policies):
            active_indicator = click.style(" (ACTIVE)", fg="green") if getattr(policy, 'is_active', False) else ""
            click.echo(f"{idx}. {click.style(policy.name, fg='blue')}{active_indicator}")
            if policy.description:
                click.echo(f"    Description: {click.style(policy.description, fg='cyan')}")
            click.echo(f"    Start rules: {click.style(str(len(policy.start_rules)), fg='green')}")
            click.echo(f"    Stop rules: {click.style(str(len(policy.stop_rules)), fg='red')}")

    click.echo("")
    click.pause("Press any key to return to the menu...")


def select_optimization_policy(
    configuration_service: ConfigurationService,
    default_id: Optional[EntityId] = None
) -> Optional[OptimizationPolicy]:
    """Select an optimization policy from the list."""
    click.echo(click.style("\n--- Select Optimization Policy ---", fg="yellow"))

    policies: List[OptimizationPolicy] = configuration_service.list_policies()
    if not policies:
        click.echo(click.style("No optimization policies found.", fg="red"))
        return None

    default_idx = ""
    for idx, policy in enumerate(policies):
        if default_id and policy.id == default_id:
            default_idx = str(idx)
        click.echo(f"{idx}. {click.style(policy.name, fg='blue')}")
        if policy.description:
            click.echo(f"    {click.style(policy.description, fg='cyan')}")

    click.echo("\nb. Back to menu\n")

    policy_idx: str = click.prompt("Choose an Optimization Policy index", type=str, default=default_idx)
    policy_idx = policy_idx.strip().lower()
    if policy_idx == "b":
        return None

    if not policy_idx.isdigit() or int(policy_idx) < 0 or int(policy_idx) >= len(policies):
        click.echo(click.style("Invalid choice. Please try again.", fg="red"))
        return None

    selected_policy = policies[int(policy_idx)]
    return selected_policy


def print_optimization_policy_details(policy: OptimizationPolicy) -> None:
    """Print the details of an optimization policy."""
    click.echo("")
    click.echo("| Name: " + click.style(policy.name, fg="blue"))
    click.echo("| ID: " + click.style(str(policy.id), fg="cyan"))
    if policy.description:
        click.echo("| Description: " + click.style(policy.description, fg="cyan"))
    
    # Show if policy is active
    active_status = "Active" if getattr(policy, 'is_active', False) else "Inactive"
    active_color = "green" if getattr(policy, 'is_active', False) else "red"
    click.echo("| Status: " + click.style(active_status, fg=active_color))
    
    click.echo("| Start Rules:")
    if policy.start_rules:
        for idx, rule in enumerate(policy.start_rules):
            click.echo(f"  {idx+1}. {click.style(rule.name, fg='green')}")
            for key, value in rule.conditions.items():
                click.echo(f"      {key}: {value}")
    else:
        click.echo("  No start rules defined")
    
    click.echo("| Stop Rules:")
    if policy.stop_rules:
        for idx, rule in enumerate(policy.stop_rules):
            click.echo(f"  {idx+1}. {click.style(rule.name, fg='red')}")
            for key, value in rule.conditions.items():
                click.echo(f"      {key}: {value}")
    else:
        click.echo("  No stop rules defined")


def update_single_optimization_policy(policy: OptimizationPolicy) -> OptimizationPolicy:
    """Update a single optimization policy."""
    click.echo(click.style(f"\n--- Update Optimization Policy: {policy.name} ---", fg="yellow"))
    
    # Note: The ConfigurationService doesn't have a direct update_policy method,
    # so we'll focus on updating rules and use the existing policy structure
    
    click.echo("Note: Policy name and description updates require recreating the policy.")
    click.echo("You can manage rules using the rule management options.")
    
    return policy


def delete_single_optimization_policy(
    policy: OptimizationPolicy,
    configuration_service: ConfigurationService,
    logger: LoggerPort
) -> bool:
    """Delete a single optimization policy."""
    click.echo(click.style(f"\n--- Delete Optimization Policy: {policy.name} ---", fg="red"))
    
    if not click.confirm(f"Are you sure you want to delete '{policy.name}'?", default=False):
        return False

    try:
        configuration_service.delete_policy(policy.id)
        click.echo(click.style("Optimization policy deleted successfully!", fg="green"))
        return True
    except (PolicyError, PolicyNotFoundError) as e:
        click.echo(click.style(f"Policy error: {str(e)}", fg="red"))
        logger.error(f"Policy error deleting optimization policy: {str(e)}")
    except Exception as e:  # Catch-all for unexpected errors
        click.echo(click.style(f"Error deleting optimization policy: {str(e)}", fg="red"))
        logger.error(f"Error deleting optimization policy: {str(e)}")
    
    return False


def manage_single_optimization_policy_menu(
    policy: OptimizationPolicy,
    configuration_service: ConfigurationService,
    logger: LoggerPort,
) -> str:
    """Menu to manage a single optimization policy."""
    while True:
        click.clear()
        click.echo(click.style(f"=== Manage Optimization Policy: {policy.name} ===", fg="yellow"))
        
        print_optimization_policy_details(policy)
        
        click.echo("\nOptions:")
        click.echo("1. Update policy (manage rules)")
        click.echo("2. Set as active policy")
        click.echo("3. Delete policy")
        click.echo("b. Back to policies menu")
        click.echo("q. Quit")

        choice = click.prompt("Choose an option", type=str, default="b")
        choice = choice.strip().lower()

        if choice == "1":
            result = manage_policy_rules_menu(policy, configuration_service, logger)
            if result == "q":
                return "q"
        elif choice == "2":
            try:
                configuration_service.set_active_policy(policy.id)
                click.echo(click.style(f"Policy '{policy.name}' set as active!", fg="green"))
            except (PolicyError, PolicyNotFoundError) as e:
                click.echo(click.style(f"Policy error: {str(e)}", fg="red"))
                logger.error(f"Policy error setting active policy: {str(e)}")
            except Exception as e:  # Catch-all for unexpected errors
                click.echo(click.style(f"Error setting active policy: {str(e)}", fg="red"))
                logger.error(f"Error setting active policy: {str(e)}")
            click.pause("Press any key to continue...")
        elif choice == "3":
            if delete_single_optimization_policy(policy, configuration_service, logger):
                return "b"  # Return to previous menu
            click.pause("Press any key to continue...")
        elif choice == "b":
            return "b"
        elif choice == "q":
            return "q"
        else:
            click.echo(click.style("Invalid choice. Please try again.", fg="red"))
            click.pause("Press any key to continue...")


def manage_policy_rules_menu(
    policy: OptimizationPolicy,
    configuration_service: ConfigurationService,
    logger: LoggerPort,
) -> str:
    """Menu to manage rules within a policy."""
    while True:
        click.clear()
        click.echo(click.style(f"=== Manage Rules for Policy: {policy.name} ===", fg="yellow"))
        
        print_optimization_policy_details(policy)
        
        click.echo("\nRule Management Options:")
        click.echo("1. Add start rule")
        click.echo("2. Add stop rule")
        click.echo("3. Edit start rule")
        click.echo("4. Edit stop rule")
        click.echo("5. Delete start rule")
        click.echo("6. Delete stop rule")
        click.echo("b. Back to policy menu")
        click.echo("q. Quit")

        choice = click.prompt("Choose an option", type=str, default="b")
        choice = choice.strip().lower()

        if choice == "1":
            add_rule_to_policy(policy, RuleType.START, configuration_service, logger)
            click.pause("Press any key to continue...")
        elif choice == "2":
            add_rule_to_policy(policy, RuleType.STOP, configuration_service, logger)
            click.pause("Press any key to continue...")
        elif choice == "3":
            edit_policy_rule(policy, RuleType.START, configuration_service, logger)
            click.pause("Press any key to continue...")
        elif choice == "4":
            edit_policy_rule(policy, RuleType.STOP, configuration_service, logger)
            click.pause("Press any key to continue...")
        elif choice == "5":
            delete_policy_rule(policy, RuleType.START, configuration_service, logger)
            click.pause("Press any key to continue...")
        elif choice == "6":
            delete_policy_rule(policy, RuleType.STOP, configuration_service, logger)
            click.pause("Press any key to continue...")
        elif choice == "b":
            return "b"
        elif choice == "q":
            return "q"
        else:
            click.echo(click.style("Invalid choice. Please try again.", fg="red"))
            click.pause("Press any key to continue...")


def add_rule_to_policy(
    policy: OptimizationPolicy,
    rule_type: RuleType,
    configuration_service: ConfigurationService,
    logger: LoggerPort
) -> None:
    """Add a rule to a policy."""
    type_name = "START" if rule_type == RuleType.START else "STOP"
    click.echo(click.style(f"\n--- Add {type_name} Rule ---", fg="yellow"))
    
    rule_name = click.prompt("Rule name", type=str)
    conditions = create_rule_conditions()
    
    if not conditions:
        click.echo(click.style("No conditions specified. Rule not created.", fg="red"))
        return
    
    try:
        configuration_service.add_rule_to_policy(
            policy_id=policy.id,
            rule_type=rule_type,
            name=rule_name,
            conditions=conditions,
            action=MiningDecision.START_MINING if rule_type == RuleType.START else MiningDecision.STOP_MINING
        )
        click.echo(click.style(f"{type_name} rule '{rule_name}' added successfully!", fg="green"))
    except (PolicyError, PolicyNotFoundError) as e:
        click.echo(click.style(f"Policy error: {str(e)}", fg="red"))
        logger.error(f"Policy error adding rule to policy: {str(e)}")
    except Exception as e:  # Catch-all for unexpected errors
        click.echo(click.style(f"Error adding rule: {str(e)}", fg="red"))
        logger.error(f"Error adding rule to policy: {str(e)}")


def edit_policy_rule(
    policy: OptimizationPolicy,
    rule_type: RuleType,
    configuration_service: ConfigurationService,
    logger: LoggerPort
) -> None:
    """Edit a rule in a policy."""
    type_name = "START" if rule_type == RuleType.START else "STOP"
    rules = policy.start_rules if rule_type == RuleType.START else policy.stop_rules
    
    if not rules:
        click.echo(click.style(f"No {type_name.lower()} rules found.", fg="red"))
        return
    
    click.echo(click.style(f"\n--- Edit {type_name} Rule ---", fg="yellow"))
    click.echo("Select a rule to edit:")
    
    for idx, rule in enumerate(rules):
        click.echo(f"{idx}. {click.style(rule.name, fg='blue')}")
    
    try:
        rule_idx = click.prompt("Choose rule index", type=int)
        if rule_idx < 0 or rule_idx >= len(rules):
            click.echo(click.style("Invalid rule index.", fg="red"))
            return
        
        selected_rule = rules[rule_idx]
        
        new_name = click.prompt("New rule name", type=str, default=selected_rule.name)
        new_conditions = create_rule_conditions()
        
        if not new_conditions:
            click.echo(click.style("No conditions specified. Rule not updated.", fg="red"))
            return
        
        configuration_service.update_policy_rule(
            policy_id=policy.id,
            rule_id=selected_rule.id,
            name=new_name,
            conditions=new_conditions,
            action=selected_rule.action
        )
        click.echo(click.style(f"Rule '{new_name}' updated successfully!", fg="green"))
        
    except (ValueError, IndexError):
        click.echo(click.style("Invalid input.", fg="red"))
    except (PolicyError, PolicyNotFoundError) as e:
        click.echo(click.style(f"Policy error: {str(e)}", fg="red"))
        logger.error(f"Policy error updating rule: {str(e)}")
    except Exception as e:  # Catch-all for unexpected errors
        click.echo(click.style(f"Error updating rule: {str(e)}", fg="red"))
        logger.error(f"Error updating rule: {str(e)}")


def delete_policy_rule(
    policy: OptimizationPolicy,
    rule_type: RuleType,
    configuration_service: ConfigurationService,
    logger: LoggerPort
) -> None:
    """Delete a rule from a policy."""
    type_name = "START" if rule_type == RuleType.START else "STOP"
    rules = policy.start_rules if rule_type == RuleType.START else policy.stop_rules
    
    if not rules:
        click.echo(click.style(f"No {type_name.lower()} rules found.", fg="red"))
        return
    
    click.echo(click.style(f"\n--- Delete {type_name} Rule ---", fg="yellow"))
    click.echo("Select a rule to delete:")
    
    for idx, rule in enumerate(rules):
        click.echo(f"{idx}. {click.style(rule.name, fg='blue')}")
    
    try:
        rule_idx = click.prompt("Choose rule index", type=int)
        if rule_idx < 0 or rule_idx >= len(rules):
            click.echo(click.style("Invalid rule index.", fg="red"))
            return
        
        selected_rule = rules[rule_idx]
        
        if not click.confirm(f"Are you sure you want to delete '{selected_rule.name}'?", default=False):
            return
        
        configuration_service.delete_policy_rule(policy_id=policy.id, rule_id=selected_rule.id)
        click.echo(click.style(f"Rule '{selected_rule.name}' deleted successfully!", fg="green"))
        
    except (ValueError, IndexError):
        click.echo(click.style("Invalid input.", fg="red"))
    except (PolicyError, PolicyNotFoundError) as e:
        click.echo(click.style(f"Policy error: {str(e)}", fg="red"))
        logger.error(f"Policy error deleting rule: {str(e)}")
    except Exception as e:  # Catch-all for unexpected errors
        click.echo(click.style(f"Error deleting rule: {str(e)}", fg="red"))
        logger.error(f"Error deleting rule: {str(e)}")


def optimization_policies_menu(configuration_service: ConfigurationService, logger: LoggerPort) -> str:
    """Main menu for managing optimization policies."""
    while True:
        click.clear()
        click.echo(click.style("--- Optimization Policies Management ---", fg="yellow"))
        click.echo("1. Add new optimization policy")
        click.echo("2. List optimization policies")
        click.echo("3. Manage existing policy")
        click.echo("b. Back to main menu")
        click.echo("q. Quit")

        choice = click.prompt("Choose an option", type=str, default="b")
        choice = choice.strip().lower()

        if choice == "1":
            handle_add_optimization_policy(configuration_service, logger)
        elif choice == "2":
            handle_list_optimization_policies(configuration_service)
        elif choice == "3":
            policy = select_optimization_policy(configuration_service)
            if policy:
                result = manage_single_optimization_policy_menu(policy, configuration_service, logger)
                if result == "q":
                    return "q"
        elif choice == "b":
            return "b"
        elif choice == "q":
            return "q"
        else:
            click.echo(click.style("Invalid choice. Please try again.", fg="red"))
            click.pause("Press any key to continue...")


def policy_menu(configuration_service: ConfigurationService, logger: LoggerPort) -> str:
    """Main policy menu."""
    while True:
        click.echo("\n" + click.style("--- POLICY & RULE ---", fg="blue", bold=True))
        click.echo("1. Add an Optimization Policy")
        click.echo("2. List all Optimization Policies")
        click.echo("3. Manage an Optimization Policy")
        click.echo("")
        click.echo("b. Back to main menu")
        click.echo("q. Quit")

        choice: str = click.prompt("Choose an option", type=str)
        choice = choice.strip().lower()

        click.clear()

        if choice == "1":
            handle_add_optimization_policy(configuration_service, logger)
        elif choice == "2":
            handle_list_optimization_policies(configuration_service)
        elif choice == "3":
            policy = select_optimization_policy(configuration_service)
            if policy is None:
                click.echo(click.style("No Optimization Policy selected. Aborting.", fg="red"))
                continue

            sub_choice = manage_single_optimization_policy_menu(
                policy,
                configuration_service, 
                logger
            )
            if sub_choice == "q":
                break
        elif choice == "b":
            break
        elif choice == "q":
            break
        else:
            click.echo(click.style("Invalid choice. Try again.", fg="red"))
            click.pause("Press any key to return to the menu...")
    return choice
