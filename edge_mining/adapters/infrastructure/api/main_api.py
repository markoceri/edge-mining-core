"""Initializes the FastAPI application for the Edge Mining system."""

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from edge_mining.application.services.adapter_service import AdapterService
from edge_mining.application.services.configuration_service import (
    ConfigurationService,
)
from edge_mining.application.services.miner_action_service import (
    MinerActionService,
)
from edge_mining.application.services.optimization_service import (
    OptimizationService,
)
from edge_mining.shared.infrastructure import Services
from edge_mining.shared.logging.port import LoggerPort

# --- Dependency Injection with FastAPI ---
# This is a common pattern using FastAPI's dependency injection system

# Define functions that provide the initialized service instances
# These would be created in __main__.py or a dedicated DI setup file


def get_adapter_service():
    """Dependency injection function to get the AdapterService."""
    # In a real app, this returns the already initialized instance
    if _api_adapter_service is None:
        raise RuntimeError("Adapter Service not initialized for API")
    return _api_adapter_service


def get_config_service():
    """Dependency injection function to get the ConfigurationService."""
    # In a real app, this returns the already initialized instance
    if _api_config_service is None:
        raise RuntimeError("Config Service not initialized for API")
    return _api_config_service


def get_miner_action_service():
    """Dependency injection function to get the ActionService."""
    if _api_miner_action_service is None:
        raise RuntimeError("Action Service not initialized for API")
    return _api_miner_action_service


def get_optimization_service():
    """Dependency injection function to get the OptimizationService."""
    if _api_optimization_service is None:
        raise RuntimeError("Optimization Service not initialized for API")
    return _api_optimization_service


# Global placeholders - Set these during app startup
_api_adapter_service: AdapterService = None
_api_config_service: ConfigurationService = None
_api_miner_action_service: MinerActionService = None
_api_optimization_service: OptimizationService = None
_api_logger: LoggerPort = None


def set_api_services(services: Services, logger: LoggerPort):
    """Set the API services using Dependency Injection."""

    _api_adapter_service = services.adapter_service
    _api_optimization_service = services.optimization_service
    _api_miner_action_service = services.miner_action_service
    _api_configuration_service = services.configuration_service
    _api_logger = logger


# --- End Dependency Injection ---


# Import routers after DI setup functions are defined
from edge_mining.adapters.domain.policy.fast_api.router import (
    router as policy_router,
)
from edge_mining.adapters.domain.miner.fast_api.router import (
    router as miner_router,
)


@asynccontextmanager
async def check_services(api_app: FastAPI):
    """Check if services are initialized before app startup."""
    # This is where we *should* initialize the services and adapters
    # For this example, we assume they are set via set_api_services() beforehand
    _api_logger.debug("FastAPI application startup...")

    if (
        _api_config_service is None
        or _api_optimization_service is None
        or _api_adapter_service is None
        or _api_miner_action_service is None
    ):
        _api_logger.error("API Services were not initialized before startup!")

    yield
    # Cleanup logic can go here if needed


app = FastAPI(
    title="Edge Mining API",
    description="API for managing and monitoring the bitcoin mining energy optimization system.",
    version="0.1.0",
    lifespan=check_services,  # Use async context manager for service checks
)

# TODO: set only localhost origins
origins = ["*"]

# User CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(miner_router, prefix="/api/v1", tags=["mining"])
app.include_router(policy_router, prefix="/api/v1", tags=["optimization_rules"])
# Add more routers here (e.g., for configuration)


@app.get("/health", tags=["system"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok"}


# Example endpoint using dependency injection
@app.post("/api/v1/evaluate", tags=["system"])
async def trigger_evaluation(
    optimization_service: Annotated[OptimizationService, Depends(get_optimization_service)],  # Inject service
):
    """Manually run all enabled optimization units."""
    _api_logger.info("API run all enabled optimization units...")
    try:
        optimization_service.run_all_enabled_units()
        return {"message": "All optimization units run successfully."}
    except Exception as e:
        _api_logger.error("Error during API run optimization units.")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {e}") from e


# --- To run this API (after setting up services): ---
# uvicorn edge_mining.adapters.infrastructure.api.main_api:app --reload
