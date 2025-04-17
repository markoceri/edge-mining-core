from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Annotated

from edge_mining.application.services.configuration_service import ConfigurationService

from edge_mining.domain.common import EntityId
from edge_mining.domain.exceptions import PolicyNotFoundError

# Import the dependency injection function defined in main_api.py
from edge_mining.adapters.infrastructure.api.main_api import get_config_service

router = APIRouter()

# We may use Pydantic models for request/response if needed
class OptimizationPolicyCreateSchema(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    is_active: bool

class OptimizationPolicyResponseSchema(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    is_active: bool

@router.get("/policies", response_model=List[OptimizationPolicyResponseSchema])
async def get_policies_list(
    config_service: Annotated[ConfigurationService, Depends(get_config_service)]
):
    """Get a list of all configured policies."""
    try:
        policies = config_service.list_policies()

        response: List[OptimizationPolicyResponseSchema] = []
        for policy in policies:
            response.append(
                OptimizationPolicyResponseSchema(
                    id=policy.id,
                    name=policy.name,
                    description=policy.description,
                    is_active=policy.is_active
                )
            )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/policies/{policy_id}", response_model=OptimizationPolicyResponseSchema)
async def get_policy_details(
    policy_id: EntityId,
    config_service: Annotated[ConfigurationService, Depends(get_config_service)]
):
    """Get details for a specific optimization policy."""
    try:
        policy = config_service.get_policy(policy_id)
        if policy is None:
            raise HTTPException(status_code=404, detail="Optimization policy not found")

        response = OptimizationPolicyResponseSchema(
            id=policy.id,
            name=policy.name,
            description=policy.description,
            is_active=policy.is_active
        )

        return response
    except PolicyNotFoundError: # Catch specific domain errors if needed
         raise HTTPException(status_code=404, detail="Policy not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


