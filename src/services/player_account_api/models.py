"""Pydantic models for Player Account API Lambda."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class PlayerStatus(str, Enum):
    """Player account status enumeration."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"
    INACTIVE = "inactive"


class CreatePlayerRequest(BaseModel):
    """Request model for creating a player account."""

    username: str = Field(min_length=3, max_length=30, description="Player username")
    email: EmailStr = Field(description="Player email address")
    display_name: str | None = Field(
        default=None, max_length=50, description="Player display name"
    )


class UpdatePlayerRequest(BaseModel):
    """Request model for updating player account."""

    display_name: str | None = Field(
        default=None, max_length=50, description="Updated display name"
    )
    email: EmailStr | None = Field(default=None, description="Updated email address")
    status: PlayerStatus | None = Field(
        default=None, description="Updated account status"
    )


class PlayerAccount(BaseModel):
    """Player account model."""

    player_id: str = Field(description="Unique player identifier")
    username: str = Field(description="Player username")
    email: EmailStr = Field(description="Player email address")
    display_name: str = Field(description="Player display name")
    status: PlayerStatus = Field(
        default=PlayerStatus.ACTIVE, description="Account status"
    )
    level: int = Field(default=1, ge=1, le=100, description="Player level")
    experience_points: int = Field(default=0, ge=0, description="Total XP")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Account creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )


class PlayerStats(BaseModel):
    """Player statistics model."""

    player_id: str = Field(description="Player identifier")
    total_games: int = Field(default=0, ge=0, description="Total games played")
    wins: int = Field(default=0, ge=0, description="Total wins")
    losses: int = Field(default=0, ge=0, description="Total losses")
    win_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Win rate")
    total_playtime_hours: int = Field(
        default=0, ge=0, description="Total playtime in hours"
    )
