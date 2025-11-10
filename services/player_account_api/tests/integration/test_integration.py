"""Integration tests for Player Account API Lambda."""

import json
from unittest.mock import MagicMock

import pytest

from services.player_account_api.handler import lambda_handler


@pytest.fixture
def lambda_context() -> MagicMock:
    """Create mock Lambda context."""
    context = MagicMock()
    context.request_id = "test-request-id"
    context.function_name = "player-account-api"
    return context


@pytest.mark.integration
class TestPlayerAccountAPIIntegration:
    """Integration tests for Player Account API Lambda end-to-end flows."""

    def test_full_player_lifecycle(self, lambda_context: MagicMock) -> None:
        """Test complete player lifecycle: create, get, update, delete."""
        # Step 1: Create player
        create_event = {
            "httpMethod": "POST",
            "path": "/players",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "username": "lifecycle_player",
                    "email": "lifecycle@example.com",
                    "display_name": "Lifecycle Test",
                }
            ),
            "pathParameters": None,
        }

        create_response = lambda_handler(create_event, lambda_context)
        assert create_response["statusCode"] == 201

        create_body = json.loads(create_response["body"])
        player_id = create_body["player_id"]

        # Step 2: Get player
        get_event = {
            "httpMethod": "GET",
            "path": f"/players/{player_id}",
            "headers": {},
            "body": None,
            "pathParameters": {"player_id": player_id},
        }

        get_response = lambda_handler(get_event, lambda_context)
        assert get_response["statusCode"] == 200

        get_body = json.loads(get_response["body"])
        assert get_body["username"] == "lifecycle_player"

        # Step 3: Update player
        update_event = {
            "httpMethod": "PUT",
            "path": f"/players/{player_id}",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"display_name": "Updated Lifecycle"}),
            "pathParameters": {"player_id": player_id},
        }

        update_response = lambda_handler(update_event, lambda_context)
        assert update_response["statusCode"] == 200

        update_body = json.loads(update_response["body"])
        assert update_body["display_name"] == "Updated Lifecycle"

        # Step 4: Get player stats
        stats_event = {
            "httpMethod": "GET",
            "path": f"/players/{player_id}/stats",
            "headers": {},
            "body": None,
            "pathParameters": {"player_id": player_id},
        }

        stats_response = lambda_handler(stats_event, lambda_context)
        assert stats_response["statusCode"] == 200

        stats_body = json.loads(stats_response["body"])
        assert stats_body["player_id"] == player_id

        # Step 5: Delete player
        delete_event = {
            "httpMethod": "DELETE",
            "path": f"/players/{player_id}",
            "headers": {},
            "body": None,
            "pathParameters": {"player_id": player_id},
        }

        delete_response = lambda_handler(delete_event, lambda_context)
        assert delete_response["statusCode"] == 204

        # Step 6: Verify player is deleted
        verify_response = lambda_handler(get_event, lambda_context)
        assert verify_response["statusCode"] == 404

    def test_list_players_after_creation(self, lambda_context: MagicMock) -> None:
        """Test listing players after creating multiple players."""
        # Create first player
        create_event_1 = {
            "httpMethod": "POST",
            "path": "/players",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"username": "player_one", "email": "one@example.com"}),
            "pathParameters": None,
        }
        lambda_handler(create_event_1, lambda_context)

        # Create second player
        create_event_2 = {
            "httpMethod": "POST",
            "path": "/players",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"username": "player_two", "email": "two@example.com"}),
            "pathParameters": None,
        }
        lambda_handler(create_event_2, lambda_context)

        # List players
        list_event = {
            "httpMethod": "GET",
            "path": "/players",
            "headers": {},
            "body": None,
            "pathParameters": None,
        }

        list_response = lambda_handler(list_event, lambda_context)
        assert list_response["statusCode"] == 200

        list_body = json.loads(list_response["body"])
        assert list_body["count"] >= 2

    def test_duplicate_username_conflict(self, lambda_context: MagicMock) -> None:
        """Test creating player with duplicate username."""
        # Create first player
        create_event = {
            "httpMethod": "POST",
            "path": "/players",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"username": "duplicate_test", "email": "dup1@example.com"}
            ),
            "pathParameters": None,
        }

        response1 = lambda_handler(create_event, lambda_context)
        assert response1["statusCode"] == 201

        # Try to create with same username
        create_event_dup = {
            "httpMethod": "POST",
            "path": "/players",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"username": "duplicate_test", "email": "dup2@example.com"}
            ),
            "pathParameters": None,
        }

        response2 = lambda_handler(create_event_dup, lambda_context)
        assert response2["statusCode"] == 409
