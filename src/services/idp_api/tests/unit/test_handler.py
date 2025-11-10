"""Unit tests for IDP API Lambda handler."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.libs.common.exceptions import ValidationException
from src.services.idp_api.handler import (
    handle_authentication,
    lambda_handler,
)
from src.services.idp_api.models import TokenResponse


@pytest.fixture
def lambda_context() -> MagicMock:
    """Create mock Lambda context."""
    context = MagicMock()
    context.request_id = "test-request-id"
    context.function_name = "idp-api"
    return context


@pytest.fixture
def auth_event() -> dict:
    """Create authentication event."""
    return {
        "httpMethod": "POST",
        "path": "/auth/token",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"username": "testuser", "password": "password123"}),
    }


@pytest.fixture
def userinfo_event() -> dict:
    """Create userinfo event."""
    return {
        "httpMethod": "GET",
        "path": "/auth/userinfo",
        "headers": {"Authorization": "Bearer test-token-123"},
        "body": "",
    }


class TestLambdaHandler:
    """Test cases for lambda_handler function."""

    @patch("src.services.idp_api.handler.IDPService")
    def test_authentication_success(
        self, mock_service: MagicMock, auth_event: dict, lambda_context: MagicMock
    ) -> None:
        """Test successful authentication."""
        # Arrange
        mock_token = TokenResponse(
            access_token="access-123",
            refresh_token="refresh-456",
            expires_in=3600,
        )
        mock_service.return_value.authenticate.return_value = mock_token

        # Act
        response = lambda_handler(auth_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["access_token"] == "access-123"
        assert body["refresh_token"] == "refresh-456"

    def test_authentication_missing_body(self, lambda_context: MagicMock) -> None:
        """Test authentication with missing body."""
        # Arrange
        event = {
            "httpMethod": "POST",
            "path": "/auth/token",
            "headers": {},
        }

        # Act
        response = lambda_handler(event, lambda_context)

        # Assert
        assert response["statusCode"] == 400

    def test_invalid_endpoint(self, lambda_context: MagicMock) -> None:
        """Test request to invalid endpoint."""
        # Arrange
        event = {
            "httpMethod": "GET",
            "path": "/invalid/path",
            "headers": {},
            "body": "",
        }

        # Act
        response = lambda_handler(event, lambda_context)

        # Assert
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["error"] == "NOT_FOUND"

    @patch("src.services.idp_api.handler.IDPService")
    def test_userinfo_success(
        self,
        mock_service: MagicMock,
        userinfo_event: dict,
        lambda_context: MagicMock,
    ) -> None:
        """Test successful userinfo retrieval."""
        # Arrange
        from src.services.idp_api.models import UserInfo

        mock_user = UserInfo(
            user_id="usr_001",
            username="testuser",
            email="test@example.com",
        )
        mock_service.return_value.get_user_info.return_value = mock_user

        # Act
        response = lambda_handler(userinfo_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["username"] == "testuser"

    def test_userinfo_missing_auth_header(self, lambda_context: MagicMock) -> None:
        """Test userinfo with missing authorization header."""
        # Arrange
        event = {
            "httpMethod": "GET",
            "path": "/auth/userinfo",
            "headers": {},
            "body": "",
        }

        # Act
        response = lambda_handler(event, lambda_context)

        # Assert
        assert response["statusCode"] == 400


class TestHandleAuthentication:
    """Test cases for handle_authentication function."""

    @patch("src.services.idp_api.handler.IDPService")
    def test_valid_credentials(self, mock_service: MagicMock) -> None:
        """Test authentication with valid credentials."""
        # Arrange
        body = {"username": "testuser", "password": "password123"}
        mock_token = TokenResponse(
            access_token="access-123",
            refresh_token="refresh-456",
            expires_in=3600,
        )
        mock_service.return_value.authenticate.return_value = mock_token

        # Act
        response = handle_authentication(body)

        # Assert
        assert response["statusCode"] == 200
        body_data = json.loads(response["body"])
        assert "access_token" in body_data

    def test_invalid_request_body(self) -> None:
        """Test authentication with invalid request body."""
        # Arrange
        body = {"username": "ab"}  # Too short

        # Act & Assert
        with pytest.raises(ValidationException):
            handle_authentication(body)
