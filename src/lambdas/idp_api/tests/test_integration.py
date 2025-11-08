"""Integration tests for IDP API Lambda."""

import json
from unittest.mock import MagicMock

import pytest

from src.lambdas.idp_api.handler import lambda_handler


@pytest.fixture
def lambda_context() -> MagicMock:
    """Create mock Lambda context."""
    context = MagicMock()
    context.request_id = "test-request-id"
    context.function_name = "idp-api"
    return context


@pytest.mark.integration
class TestIDPAPIIntegration:
    """Integration tests for IDP API Lambda end-to-end flows."""

    def test_full_authentication_flow(self, lambda_context: MagicMock) -> None:
        """Test complete authentication flow from login to user info retrieval."""
        # Step 1: Authenticate
        auth_event = {
            "httpMethod": "POST",
            "path": "/auth/token",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"username": "testuser", "password": "password123"}),
        }

        auth_response = lambda_handler(auth_event, lambda_context)
        assert auth_response["statusCode"] == 200

        auth_body = json.loads(auth_response["body"])
        access_token = auth_body["access_token"]
        refresh_token = auth_body["refresh_token"]

        # Step 2: Get user info using access token
        userinfo_event = {
            "httpMethod": "GET",
            "path": "/auth/userinfo",
            "headers": {"Authorization": f"Bearer {access_token}"},
            "body": "",
        }

        userinfo_response = lambda_handler(userinfo_event, lambda_context)
        assert userinfo_response["statusCode"] == 200

        userinfo_body = json.loads(userinfo_response["body"])
        assert userinfo_body["username"] == "testuser"
        assert userinfo_body["email"] == "testuser@example.com"

        # Step 3: Refresh token
        refresh_event = {
            "httpMethod": "POST",
            "path": "/auth/refresh",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"refresh_token": refresh_token}),
        }

        refresh_response = lambda_handler(refresh_event, lambda_context)
        assert refresh_response["statusCode"] == 200

        refresh_body = json.loads(refresh_response["body"])
        new_access_token = refresh_body["access_token"]
        assert new_access_token != access_token

    def test_invalid_credentials_flow(self, lambda_context: MagicMock) -> None:
        """Test authentication with invalid credentials."""
        # Arrange
        auth_event = {
            "httpMethod": "POST",
            "path": "/auth/token",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"username": "testuser", "password": "wrongpassword"}
            ),
        }

        # Act
        response = lambda_handler(auth_event, lambda_context)

        # Assert
        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert "error" in body

    def test_unauthorized_userinfo_access(self, lambda_context: MagicMock) -> None:
        """Test accessing user info without valid token."""
        # Arrange
        userinfo_event = {
            "httpMethod": "GET",
            "path": "/auth/userinfo",
            "headers": {"Authorization": "Bearer invalid-token"},
            "body": "",
        }

        # Act
        response = lambda_handler(userinfo_event, lambda_context)

        # Assert
        assert response["statusCode"] == 401
