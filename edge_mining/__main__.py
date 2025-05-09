"""Start Edge Mining."""

import sys
import os
import uvicorn
import asyncio

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

settings = AppSettings()
logger = TerminalLogger(LOG_LEVEL=settings.log_level)

async def main_async():
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
        mode = "standard" # Default mode

    logger.info(f"Running in '{mode}' mode.")
    
    if mode == "standard":
        # --- Run the FastAPI server ---
        logger.debug("Starting FastAPI server with Uvicorn...")
        # Note: Uvicorn might reload and cause DI to run multiple times if --reload is used.
        # We should to consider more robust DI setup for production APIs.
        api_config = uvicorn.Config(
            fastapi_app,
            host="0.0.0.0",
            port=settings.api_port,
            log_level=settings.log_level.lower()
        )
        api_server = uvicorn.Server(api_config)
        
        # --- Run the main automation loop ---
        scheduler = AutomationScheduler(
            orchestrator=orchestrator_service,
            logger=logger,
            settings=settings
        )
        
        await asyncio.gather(
            api_server.serve(), # Run the FastAPI server
            scheduler.start()   # Run the automation scheduler
        )
    
    elif mode == "cli":
        # Run Click CLI
        cli()

    else:
        logger.error(f"Unknown run mode: '{mode}'. Use 'standard', or 'cli'.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user.")
    except Exception as e:
        logger.error(f"Unhandled exception during main execution: {e}")
    finally:
        # Sure to flush logs before exiting
        logger.shutdown()
        sys.exit(1)
