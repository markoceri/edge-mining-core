"""Pydantic models for miner domain"""

from pydantic import BaseModel
from typing import List, Optional, Annotated

class MinerCreateSchema(BaseModel):
    miner_id: str
    name: str
    ip_address: Optional[str] = None

class MinerResponseSchema(BaseModel):
    id: str
    name: str
    ip_address: Optional[str] = None
    status: str # Use enum name