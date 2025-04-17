"""Start Edge Minig."""

import sys
import os
import uvicorn

# Ensure the src directory is in the Python path
# This is often needed when running directly with `python -m edge_mining`
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from edge_mining.adapters.infrastructure.sheduler.jobs import AutomationScheduler
from edge_mining.adapters.infrastructure.logging.terminal_logging import TerminalLogger
from edge_mining.shared.settings.settings import AppSettings

from edge_mining.adapters.infrastructure.cli.commands import cli, set_cli_services
from edge_mining.adapters.infrastructure.api.main_api import app as fastapi_app, set_api_services

from edge_mining.bootstrap import configure_dependencies

logger = TerminalLogger()
settings = AppSettings()

def main():
    logger.welcome()
    
    # --- Dependency Injection ---
    try:
        config_service, orchestrator_service = configure_dependencies(logger, settings)
    except Exception as e:
        logger.critical("Failed to configure dependencies. Exiting.")
        sys.exit(1)
        
    # Inject services into CLI and API
    set_cli_services(config_service, orchestrator_service, logger)
    set_api_services(config_service, orchestrator_service, logger)
    
    # --- Determine Run Mode ---
    # Example: Use command-line argument to choose mode
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        # Remove mode argument so Click/FastAPI don't see it
        sys.argv.pop(1)
    else:
        mode = "scheduler" # Default mode

    logger.info(f"Running in '{mode}' mode.")
    
    if mode == "scheduler":
        # Run the main automation loop
        scheduler = AutomationScheduler(
            orchestrator=orchestrator_service,
            logger=logger,
            settings=settings
        )

        scheduler.start() # This blocks until interrupted
    
    elif mode == "cli":
        # Run Click CLI
        cli()

    elif mode == "api":
        logger.info("Starting FastAPI server with Uvicorn...")
        # Note: Uvicorn might reload and cause DI to run multiple times if --reload is used.
        # We should to consider more robust DI setup for production APIs.
        uvicorn.run(fastapi_app, host="0.0.0.0", port=settings.api_port, log_level=settings.log_level.lower())

    else:
        logger.error(f"Unknown run mode: '{mode}'. Use 'scheduler', 'cli', or 'api'.")
        sys.exit(1)
    
    logger.info("Edge Mining is closing, bye! 🫶​")

if __name__ == "__main__":
    main()
