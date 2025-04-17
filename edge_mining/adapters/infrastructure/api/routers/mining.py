from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Annotated

from edge_mining.application.services.configuration_service import ConfigurationService

from edge_mining.domain.miner.common import MinerId
from edge_mining.domain.exceptions import MinerNotFoundError

# Import the dependency injection function defined in main_api.py
from edge_mining.adapters.infrastructure.api.main_api import get_config_service

router = APIRouter()

# We may use Pydantic models for request/response if needed
class MinerCreateSchema(BaseModel):
    miner_id: str
    name: str
    ip_address: Optional[str] = None

class MinerResponseSchema(BaseModel):
    id: str
    name: str
    ip_address: Optional[str] = None
    status: str # Use enum name

@router.get("/miners", response_model=List[MinerResponseSchema]) # Use DTOs directly or a Pydantic schema
async def get_miners_list(
    config_service: Annotated[ConfigurationService, Depends(get_config_service)]
):
    """Get a list of all configured miners."""
    try:
        miners = config_service.list_miners()

        # Convert to response schema
        response_miners = []
        for miner in miners:
            response_miners.append(
                MinerResponseSchema(
                    id=miner.id,
                    name=miner.name,
                    status=miner.status,
                    ip_address=miner.ip_address
                )
            )

        return response_miners
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/miners/{miner_id}", response_model=MinerCreateSchema)
async def get_miner_details(
    miner_id: MinerId,
    config_service: Annotated[ConfigurationService, Depends(get_config_service)]
):
    """Get details for a specific miner."""
    try:
        miner = config_service.get_miner(miner_id)
        if miner is None:
            raise HTTPException(status_code=404, detail="Miner not found")

        response = MinerCreateSchema(
            id=miner.id,
            name=miner.name,
            ip_address=miner.ip_address
        )

        return response
    except MinerNotFoundError: # Catch specific domain errors if needed
         raise HTTPException(status_code=404, detail="Miner not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# TODO: Add POST endpoint to add miners (use request schema)
# TODO: Add DELETE endpoint to remove miners