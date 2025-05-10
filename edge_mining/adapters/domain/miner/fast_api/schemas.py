"""Pydantic models for miner domain"""

from pydantic import BaseModel
from typing import List, Optional, Annotated

class MinerResponseSchema(BaseModel):
    id: str
    name: str
    status: str
    ip_address: Optional[str] = None
    power_consumption: Optional[str] = None

class MinerCreateSchema(BaseModel):
    name: str
    ip_address: Optional[str] = None
    power_consumption: Optional[str] = None

class MinerUpdateSchema(BaseModel):
    name: str
    status: str
    ip_address: Optional[str] = None
    power_consumption: Optional[str] = None

class MinerStatusSchema(BaseModel):
    id: str
    status: str
    power_consumption: Optional[str] = None