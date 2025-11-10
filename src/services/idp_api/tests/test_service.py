"""Unit tests for IDP API service."""

import pytest

from src.services.idp_api.service import IDPService
from src.libs.common.exceptions import AuthenticationException, NotFoundException


class TestIDPService:
    """Test cases for IDPService class."""

    def test_authenticate_valid_credentials(self) -> None:
        """Test authentication with valid credentials."""
        # Arrange
        service = IDPService()
        username = "testuser"
        password = "password123"

        # Act
        token_response = service.authenticate(username, password)

        # Assert
        assert token_response.access_token is not None
        assert token_response.refresh_token is not None
        assert token_response.expires_in == 3600
        assert token_response.token_type == "Bearer"

    def test_authenticate_invalid_username(self) -> None:
        """Test authentication with invalid username."""
        # Arrange
        service = IDPService()

        # Act & Assert
        with pytest.raises(AuthenticationException) as exc_info:
            service.authenticate("invaliduser", "password123")
        assert "Invalid username or password" in str(exc_info.value)

    def test_authenticate_invalid_password(self) -> None:
        """Test authentication with invalid password."""
        # Arrange
        service = IDPService()

        # Act & Assert
        with pytest.raises(AuthenticationException) as exc_info:
            service.authenticate("testuser", "wrongpassword")
        assert "Invalid username or password" in str(exc_info.value)

    def test_get_user_info_valid_token(self) -> None:
        """Test getting user info with valid token."""
        # Arrange
        service = IDPService()
        token_response = service.authenticate("testuser", "password123")

        # Act
        user_info = service.get_user_info(token_response.access_token)

        # Assert
        assert user_info.username == "testuser"
        assert user_info.email == "testuser@example.com"
        assert user_info.is_active is True

    def test_get_user_info_invalid_token(self) -> None:
        """Test getting user info with invalid token."""
        # Arrange
        service = IDPService()

        # Act & Assert
        with pytest.raises(AuthenticationException) as exc_info:
            service.get_user_info("invalid-token")
        assert "Invalid or expired token" in str(exc_info.value)

    def test_get_user_info_wrong_token_type(self) -> None:
        """Test getting user info with refresh token instead of access token."""
        # Arrange
        service = IDPService()
        token_response = service.authenticate("testuser", "password123")

        # Act & Assert
        with pytest.raises(AuthenticationException) as exc_info:
            service.get_user_info(token_response.refresh_token)  # type: ignore
        assert "Invalid token type" in str(exc_info.value)

    def test_refresh_token_valid(self) -> None:
        """Test token refresh with valid refresh token."""
        # Arrange
        service = IDPService()
        initial_token = service.authenticate("testuser", "password123")

        # Act
        new_token = service.refresh_token(initial_token.refresh_token)  # type: ignore

        # Assert
        assert new_token.access_token is not None
        assert new_token.access_token != initial_token.access_token
        assert new_token.expires_in == 3600

    def test_refresh_token_invalid(self) -> None:
        """Test token refresh with invalid token."""
        # Arrange
        service = IDPService()

        # Act & Assert
        with pytest.raises(AuthenticationException) as exc_info:
            service.refresh_token("invalid-refresh-token")
        assert "Invalid refresh token" in str(exc_info.value)

    def test_refresh_token_wrong_type(self) -> None:
        """Test token refresh with access token instead of refresh token."""
        # Arrange
        service = IDPService()
        token_response = service.authenticate("testuser", "password123")

        # Act & Assert
        with pytest.raises(AuthenticationException) as exc_info:
            service.refresh_token(token_response.access_token)
        assert "Invalid token type" in str(exc_info.value)
