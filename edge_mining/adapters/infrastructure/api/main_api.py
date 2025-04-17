from fastapi import FastAPI, Depends, HTTPException
from typing import Annotated

from edge_mining.application.services.configuration_service import ConfigurationService
from edge_mining.application.services.mining_orchestrator import MiningOrchestratorService
from edge_mining.shared.logging.port import LoggerPort

# --- Placeholder for Dependency Injection with FastAPI ---
# This is a common pattern using FastAPI's dependency injection system

# Define functions that provide the initialized service instances
# These would be created in __main__.py or a dedicated DI setup file

def get_config_service():
    # In a real app, this returns the already initialized instance
    if _api_config_service is None:
         raise RuntimeError("Config Service not initialized for API")
    return _api_config_service

def get_orchestrator_service():
    if _api_orchestrator_service is None:
         raise RuntimeError("Orchestrator Service not initialized for API")
    return _api_orchestrator_service

# Global placeholders - Set these during app startup
_api_config_service: ConfigurationService = None
_api_orchestrator_service: MiningOrchestratorService = None

def set_api_services(
        config_service: ConfigurationService,
        orchestrator_service: MiningOrchestratorService,
        logger: LoggerPort
    ):
    global _api_config_service, _api_orchestrator_service, _logger

    _api_config_service = config_service
    _api_orchestrator_service = orchestrator_service
    _logger = logger

# --- End Placeholder ---

# Import routers after DI setup functions are defined
from .routers import mining, policy

app = FastAPI(
    title="Edge Mining API",
    description="API for managing and monitoring the bitcoin mining energy optimization system.",
    version="0.1.0"
)

# Include routers
app.include_router(mining.router, prefix="/api/v1", tags=["mining"])
app.include_router(policy.router, prefix="/api/v1", tags=["optimization_rules"])
# Add more routers here (e.g., for configuration)

@app.on_event("startup")
async def startup_event():
    # This is where we *should* initialize the services and adapters
    # For this example, we assume they are set via set_api_services() beforehand
    _logger.debug("FastAPI application startup...")
    
    if _api_config_service is None or _api_orchestrator_service is None:
        _logger.error("API Services were not initialized before startup!")

@app.get("/health", tags=["system"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok"}

# Example endpoint using dependency injection
@app.post("/api/v1/evaluate", tags=["system"])
async def trigger_evaluation(
    orchestrator: Annotated[MiningOrchestratorService, Depends(get_orchestrator_service)] # Inject service
):
    """Manually trigger one evaluation cycle."""
    _logger.info("API triggered evaluation cycle...")
    try:
        orchestrator.evaluate_and_control_miners()
        return {"message": "Evaluation cycle triggered successfully."}
    except Exception as e:
        _logger.error("Error during API triggered evaluation:")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {e}")


# --- To run this API (after setting up services): ---
# uvicorn edge_mining.adapters.infrastructure.api.main_api:app --reload