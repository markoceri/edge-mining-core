"""Pydantic models for miner domain"""

from pydantic import BaseModel
from typing import List, Optional, Annotated

from edge_mining.domain.miner.value_objects import HashRate

class MinerResponseSchema(BaseModel):
    id: str
    name: str
    status: str
    active: bool
    ip_address: Optional[str] = None
    hash_rate: Optional[HashRate] = None
    hash_rate_max: Optional[HashRate] = None
    power_consumption: Optional[float] = None
    power_consumption_max: Optional[float] = None

class MinerCreateSchema(BaseModel):
    name: str
    active: bool
    ip_address: Optional[str] = None
    hash_rate_max: Optional[HashRate] = None
    power_consumption_max: Optional[float] = None

class MinerUpdateSchema(BaseModel):
    name: str
    active: bool
    ip_address: Optional[str] = None
    hash_rate_max: Optional[HashRate] = None
    power_consumption_max: Optional[float] = None

class MinerStatusSchema(BaseModel):
    id: str
    status: str
    active: bool
    hash_rate: Optional[HashRate] = None
    power_consumption: Optional[float] = None