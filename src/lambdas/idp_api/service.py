"""Business logic for IDP API."""

import secrets
import time
from datetime import datetime, timedelta

from src.lambdas.idp_api.models import TokenResponse, UserInfo
from src.shared.exceptions import AuthenticationException, NotFoundException
from src.shared.logger import get_logger

logger = get_logger(__name__)


class IDPService:
    """Service class for Identity Provider operations."""

    # In-memory storage for demo purposes - replace with DynamoDB in production
    _users = {
        "testuser": {
            "user_id": "usr_001",
            "username": "testuser",
            "password": "password123",  # noqa: S105 - This is a demo password
            "email": "testuser@example.com",
            "is_active": True,
            "created_at": datetime.utcnow(),
        }
    }

    _tokens: dict[str, dict[str, str]] = {}

    def authenticate(self, username: str, password: str) -> TokenResponse:
        """
        Authenticate user and generate tokens.

        Args:
            username: Username for authentication
            password: User password

        Returns:
            TokenResponse: Token response with access and refresh tokens

        Raises:
            AuthenticationException: When authentication fails
        """
        logger.info("Authentication attempt", extra={"username": username})

        # Validate credentials
        user = self._users.get(username)
        if not user or user["password"] != password:
            logger.warning("Authentication failed", extra={"username": username})
            raise AuthenticationException("Invalid username or password")

        if not user["is_active"]:
            raise AuthenticationException("Account is not active")

        # Generate tokens
        access_token = self._generate_token()
        refresh_token = self._generate_token()

        # Store token mapping
        self._tokens[access_token] = {
            "user_id": user["user_id"],
            "username": username,
            "type": "access",
            "expires_at": str(int(time.time()) + 3600),
        }
        self._tokens[refresh_token] = {
            "user_id": user["user_id"],
            "username": username,
            "type": "refresh",
            "expires_at": str(int(time.time()) + 86400),
        }

        logger.info("Authentication successful", extra={"username": username})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=3600,
        )

    def get_user_info(self, token: str) -> UserInfo:
        """
        Get user information from access token.

        Args:
            token: Access token

        Returns:
            UserInfo: User information

        Raises:
            AuthenticationException: When token is invalid
            NotFoundException: When user not found
        """
        # Validate token
        token_data = self._tokens.get(token)
        if not token_data:
            raise AuthenticationException("Invalid or expired token")

        if token_data["type"] != "access":
            raise AuthenticationException("Invalid token type")

        # Check expiration
        if int(token_data["expires_at"]) < int(time.time()):
            raise AuthenticationException("Token has expired")

        # Get user
        username = token_data["username"]
        user = self._users.get(username)
        if not user:
            raise NotFoundException("User not found")

        return UserInfo(
            user_id=user["user_id"],
            username=user["username"],
            email=user["email"],
            is_active=user["is_active"],
            created_at=user["created_at"],
        )

    def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            TokenResponse: New token response

        Raises:
            AuthenticationException: When refresh token is invalid
        """
        # Validate refresh token
        token_data = self._tokens.get(refresh_token)
        if not token_data:
            raise AuthenticationException("Invalid refresh token")

        if token_data["type"] != "refresh":
            raise AuthenticationException("Invalid token type")

        # Check expiration
        if int(token_data["expires_at"]) < int(time.time()):
            raise AuthenticationException("Refresh token has expired")

        # Generate new access token
        access_token = self._generate_token()
        self._tokens[access_token] = {
            "user_id": token_data["user_id"],
            "username": token_data["username"],
            "type": "access",
            "expires_at": str(int(time.time()) + 3600),
        }

        logger.info(
            "Token refreshed", extra={"username": token_data["username"]}
        )

        return TokenResponse(
            access_token=access_token,
            expires_in=3600,
        )

    @staticmethod
    def _generate_token() -> str:
        """
        Generate a secure random token.

        Returns:
            str: Random token string
        """
        return secrets.token_urlsafe(32)
