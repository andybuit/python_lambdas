"""Pydantic models for IDP API Lambda."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class AuthenticationRequest(BaseModel):
    """Request model for user authentication."""

    username: str = Field(min_length=3, max_length=50, description="Username")
    password: str = Field(min_length=8, description="User password")
    grant_type: str = Field(default="password", description="OAuth2 grant type")


class TokenResponse(BaseModel):
    """Response model for authentication token."""

    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(default=3600, description="Token expiration in seconds")
    refresh_token: str | None = Field(
        default=None, description="Refresh token if applicable"
    )
    issued_at: datetime = Field(
        default_factory=datetime.utcnow, description="Token issuance timestamp"
    )


class UserInfo(BaseModel):
    """User information model."""

    user_id: str = Field(description="Unique user identifier")
    username: str = Field(description="Username")
    email: EmailStr = Field(description="User email address")
    is_active: bool = Field(default=True, description="User active status")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Account creation timestamp"
    )


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""

    refresh_token: str = Field(description="Refresh token")
    grant_type: str = Field(default="refresh_token", description="Grant type")
