"""Pydantic models for policy domain"""

from typing import List, Optional
from enum import Enum
from pydantic import BaseModel

from edge_mining.domain.policy.common import MiningDecision

class OptimizationPolicyCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None
    target_miner_ids: List[str]

class OptimizationPolicyResponseSchema(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    target_miner_ids: List[str]
    is_active: bool

class RuleTypeSchema(str, Enum):
    start = "start"
    stop = "stop"

class MiningDecisionSchema(str, Enum):
    start_mining = "start_mining"
    stop_mining = "stop_mining"
    maintain_state = "maintain_state"

class AutomationRuleResponseSchema(BaseModel):
    id: str
    name: str
    conditions: dict # Define the structure of conditions if needed
    action: MiningDecisionSchema # Use enum name

class AutomationRuleCreateSchema(BaseModel):
    name: str
    conditions: dict
    action: MiningDecisionSchema # Use enum name
