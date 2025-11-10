"""Unit tests for Player Account API Lambda handler."""

import json
from unittest.mock import MagicMock, patch

import pytest

from services.player_account_api.handler import lambda_handler
from services.player_account_api.models import PlayerAccount, PlayerStatus


@pytest.fixture
def lambda_context() -> MagicMock:
    """Create mock Lambda context."""
    context = MagicMock()
    context.request_id = "test-request-id"
    context.function_name = "player-account-api"
    return context


@pytest.fixture
def create_player_event() -> dict:
    """Create player creation event."""
    return {
        "httpMethod": "POST",
        "path": "/players",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {
                "username": "newplayer",
                "email": "player@example.com",
                "display_name": "New Player",
            }
        ),
        "pathParameters": None,
    }


@pytest.fixture
def get_player_event() -> dict:
    """Create get player event."""
    return {
        "httpMethod": "GET",
        "path": "/players/plr_123",
        "headers": {},
        "body": None,
        "pathParameters": {"player_id": "plr_123"},
    }


class TestPlayerAccountHandler:
    """Test cases for Player Account Lambda handler."""

    @patch("services.player_account_api.handler.PlayerAccountService")
    def test_create_player_success(
        self,
        mock_service: MagicMock,
        create_player_event: dict,
        lambda_context: MagicMock,
    ) -> None:
        """Test successful player creation."""
        # Arrange
        mock_player = PlayerAccount(
            player_id="plr_123",
            username="newplayer",
            email="player@example.com",
            display_name="New Player",
        )
        mock_service.return_value.create_player.return_value = mock_player

        # Act
        response = lambda_handler(create_player_event, lambda_context)

        # Assert
        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        assert body["username"] == "newplayer"

    @patch("services.player_account_api.handler.PlayerAccountService")
    def test_get_player_success(
        self,
        mock_service: MagicMock,
        get_player_event: dict,
        lambda_context: MagicMock,
    ) -> None:
        """Test successful player retrieval."""
        # Arrange
        mock_player = PlayerAccount(
            player_id="plr_123",
            username="testplayer",
            email="test@example.com",
            display_name="Test Player",
        )
        mock_service.return_value.get_player.return_value = mock_player

        # Act
        response = lambda_handler(get_player_event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["player_id"] == "plr_123"

    def test_invalid_endpoint(self, lambda_context: MagicMock) -> None:
        """Test request to invalid endpoint."""
        # Arrange
        event = {
            "httpMethod": "POST",
            "path": "/invalid/path",
            "headers": {},
            "body": "{}",
            "pathParameters": None,
        }

        # Act
        response = lambda_handler(event, lambda_context)

        # Assert
        assert response["statusCode"] == 404

    @patch("services.player_account_api.handler.PlayerAccountService")
    def test_update_player_success(
        self, mock_service: MagicMock, lambda_context: MagicMock
    ) -> None:
        """Test successful player update."""
        # Arrange
        event = {
            "httpMethod": "PUT",
            "path": "/players/plr_123",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"display_name": "Updated Name"}),
            "pathParameters": {"player_id": "plr_123"},
        }

        mock_player = PlayerAccount(
            player_id="plr_123",
            username="testplayer",
            email="test@example.com",
            display_name="Updated Name",
        )
        mock_service.return_value.update_player.return_value = mock_player

        # Act
        response = lambda_handler(event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["display_name"] == "Updated Name"

    @patch("services.player_account_api.handler.PlayerAccountService")
    def test_delete_player_success(
        self, mock_service: MagicMock, lambda_context: MagicMock
    ) -> None:
        """Test successful player deletion."""
        # Arrange
        event = {
            "httpMethod": "DELETE",
            "path": "/players/plr_123",
            "headers": {},
            "body": None,
            "pathParameters": {"player_id": "plr_123"},
        }

        mock_service.return_value.delete_player.return_value = None

        # Act
        response = lambda_handler(event, lambda_context)

        # Assert
        assert response["statusCode"] == 204

    @patch("services.player_account_api.handler.PlayerAccountService")
    def test_list_players_success(
        self, mock_service: MagicMock, lambda_context: MagicMock
    ) -> None:
        """Test successful player listing."""
        # Arrange
        event = {
            "httpMethod": "GET",
            "path": "/players",
            "headers": {},
            "body": None,
            "pathParameters": None,
        }

        mock_players = [
            PlayerAccount(
                player_id="plr_1",
                username="player1",
                email="p1@example.com",
                display_name="Player 1",
            ),
            PlayerAccount(
                player_id="plr_2",
                username="player2",
                email="p2@example.com",
                display_name="Player 2",
            ),
        ]
        mock_service.return_value.list_players.return_value = mock_players

        # Act
        response = lambda_handler(event, lambda_context)

        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["count"] == 2
        assert len(body["players"]) == 2
