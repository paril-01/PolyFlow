"""Data model for Regional Currency Detect."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4


class RegionalCurrencyDetectRequest(BaseModel):
    """Input request model for Regional Currency Detect."""
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: dict = Field(default_factory=dict)
    metadata: Optional[dict] = None


class RegionalCurrencyDetectResponse(BaseModel):
    """Output response model for Regional Currency Detect."""
    id: UUID
    status: str = "success"
    result: Optional[dict] = None
    processing_time_ms: float = 0.0
    errors: List[str] = Field(default_factory=list)
