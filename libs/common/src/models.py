"""Shared Pydantic models for request/response validation."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class APIResponse(BaseModel):
    """Standard API response model."""

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    success: bool = Field(description="Whether the request was successful")
    message: str = Field(description="Human-readable message")
    data: dict[str, Any] | None = Field(
        default=None, description="Response payload data"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


class ErrorResponse(BaseModel):
    """Standard error response model."""

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    error: str = Field(description="Error type or code")
    message: str = Field(description="Error message")
    details: dict[str, Any] | None = Field(
        default=None, description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )
