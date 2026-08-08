"""Data model for Restock Auto Trigger."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4


class RestockAutoTriggerRequest(BaseModel):
    """Input request model for Restock Auto Trigger."""
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: dict = Field(default_factory=dict)
    metadata: Optional[dict] = None


class RestockAutoTriggerResponse(BaseModel):
    """Output response model for Restock Auto Trigger."""
    id: UUID
    status: str = "success"
    result: Optional[dict] = None
    processing_time_ms: float = 0.0
    errors: List[str] = Field(default_factory=list)
