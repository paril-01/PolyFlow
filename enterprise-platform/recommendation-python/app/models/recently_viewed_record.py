"""Data model for Recently Viewed Record."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4


class RecentlyViewedRecordRequest(BaseModel):
    """Input request model for Recently Viewed Record."""
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: dict = Field(default_factory=dict)
    metadata: Optional[dict] = None


class RecentlyViewedRecordResponse(BaseModel):
    """Output response model for Recently Viewed Record."""
    id: UUID
    status: str = "success"
    result: Optional[dict] = None
    processing_time_ms: float = 0.0
    errors: List[str] = Field(default_factory=list)
