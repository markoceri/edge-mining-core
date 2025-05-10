"""API Router for miner domain"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Annotated

from edge_mining.application.services.configuration_service import ConfigurationService
from edge_mining.application.services.action_service import ActionService

from edge_mining.domain.miner.common import MinerId
from edge_mining.domain.exceptions import MinerNotFoundError

from edge_mining.adapters.domain.miner.fast_api.schemas import (
    MinerResponseSchema, MinerCreateSchema, MinerUpdateSchema,
    MinerStatusSchema
)

# Import the dependency injection function defined in main_api.py
from edge_mining.adapters.infrastructure.api.main_api import get_config_service
from edge_mining.adapters.infrastructure.api.main_api import get_action_service

router = APIRouter()

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
                    power_consumption=miner.power_consumption,
                    ip_address=miner.ip_address
                )
            )

        return response_miners
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/miners/{miner_id}", response_model=MinerResponseSchema)
async def get_miner_details(
    miner_id: MinerId,
    config_service: Annotated[ConfigurationService, Depends(get_config_service)]
):
    """Get details for a specific miner."""
    try:
        miner = config_service.get_miner(miner_id)

        response = MinerResponseSchema(
            id=miner.id,
            name=miner.name,
            ip_address=miner.ip_address,
            status=miner.status,
            power_consumption=miner.power_consumption
        )

        return response
    except MinerNotFoundError: # Catch specific domain errors if needed
         raise HTTPException(status_code=404, detail="Miner not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/miners", response_model=MinerResponseSchema)
async def add_miner(
    miner: MinerCreateSchema,
    config_service: Annotated[ConfigurationService, Depends(get_config_service)]
):
    """Add a new miner."""
    try:
        new_miner = config_service.add_miner(
            name=miner.name,
            ip_address=miner.ip_address,
            power_consumption=miner.power_consumption
        )

        response = MinerResponseSchema(
            id=new_miner.id,
            name=new_miner.name,
            status=new_miner.status,
            ip_address=new_miner.ip_address,
            power_consumption=new_miner.power_consumption
        )

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/miners/{miner_id}", response_model=MinerResponseSchema)
async def remove_miner(
    miner_id: MinerId,
    config_service: Annotated[ConfigurationService, Depends(get_config_service)]
):
    """Remove a miner."""
    try:
        deleted_miner = config_service.remove_miner(miner_id)
        
        response = MinerResponseSchema(
            id=deleted_miner.id,
            name=deleted_miner.name,
            status=deleted_miner.status,
            ip_address=deleted_miner.ip_address,
            power_consumption=deleted_miner.power_consumption
        )

        return response
    except MinerNotFoundError:
        raise HTTPException(status_code=404, detail="Miner not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/miners/{miner_id}", response_model=MinerResponseSchema)
async def update_miner(
    miner_id: MinerId,
    miner_update: MinerUpdateSchema,
    config_service: Annotated[ConfigurationService, Depends(get_config_service)]
):
    """Update a miner's details."""
    try:
        miner = config_service.get_miner(miner_id)

        miner_updated = config_service.update_miner(
            miner_id=miner.id,
            name=miner_update.name,
            ip_address=miner_update.ip_address,
            power_consumption=miner_update.power_consumption
        )

        response = MinerResponseSchema(
            id=miner_updated.id,
            name=miner_updated.name,
            status=miner_updated.status,
            ip_address=miner_updated.ip_address,
            power_consumption=miner_updated.power_consumption
        )

        return response
    except MinerNotFoundError:
        raise HTTPException(status_code=404, detail="Miner not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/miners/{miner_id}/start", response_model=MinerStatusSchema)
async def start_miner(
    miner_id: MinerId,
    action_service: Annotated[ActionService, Depends(get_action_service)],
    config_service: Annotated[ConfigurationService, Depends(get_config_service)]
):
    """Start a miner."""
    try:
        success = action_service.start_miner(miner_id)
        
        if success:
            miner = config_service.get_miner(miner_id)
            
            response = MinerStatusSchema(
                id=miner.id,
                status=miner.status,
                power_consumption=miner.power_consumption
            )
            
            return response
        else:
            raise HTTPException(status_code=500, detail="Failed to start miner")
    except MinerNotFoundError:
        raise HTTPException(status_code=404, detail="Miner not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/miners/{miner_id}/stop", response_model=MinerStatusSchema)
async def stop_miner(
    miner_id: MinerId,
    action_service: Annotated[ActionService, Depends(get_action_service)],
    config_service: Annotated[ConfigurationService, Depends(get_config_service)]
):
    """Stop a miner."""
    try:
        success = action_service.stop_miner(miner_id)
        
        if success:
            miner = config_service.get_miner(miner_id)
            
            response = MinerStatusSchema(
                id=miner.id,
                status=miner.status,
                power_consumption=miner.power_consumption
            )
            
            return response
        else:
            raise HTTPException(status_code=500, detail="Failed to stop miner")
    except MinerNotFoundError:
        raise HTTPException(status_code=404, detail="Miner not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/miners/{miner_id}/status", response_model=MinerStatusSchema)
async def get_miner_status(
    miner_id: MinerId,
    action_service: Annotated[ActionService, Depends(get_action_service)],
    config_service: Annotated[ConfigurationService, Depends(get_config_service)]
):
    """Get the current status of a miner."""
    try:
        miner = config_service.get_miner(miner_id)
        
        response = MinerStatusSchema(
            id=miner.id,
            status=miner.status,
            power_consumption=miner.power_consumption
        )
        
        return response
    except MinerNotFoundError:
        raise HTTPException(status_code=404, detail="Miner not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))