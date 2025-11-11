"""Unit tests for Player Account API service."""

import pytest
from libs.common.src.exceptions import ConflictException, NotFoundException

from services.player_account_api.src.models import (
    PlayerStatus,
    UpdatePlayerRequest,
)
from services.player_account_api.src.service import PlayerAccountService


class TestPlayerAccountService:
    """Test cases for PlayerAccountService class."""

    def setup_method(self) -> None:
        """Reset storage before each test."""
        self.service = PlayerAccountService(reset_storage=True)

    def test_create_player_success(self) -> None:
        """Test successful player creation."""
        # Act
        player = self.service.create_player(
            username="testplayer", email="test@example.com", display_name="Test Player"
        )

        # Assert
        assert player.username == "testplayer"
        assert player.email == "test@example.com"
        assert player.display_name == "Test Player"
        assert player.status == PlayerStatus.ACTIVE
        assert player.player_id.startswith("plr_")

    def test_create_player_duplicate_username(self) -> None:
        """Test creating player with duplicate username."""
        # Arrange
        self.service.create_player(username="testplayer", email="test1@example.com")

        # Act & Assert
        with pytest.raises(ConflictException) as exc_info:
            self.service.create_player(username="testplayer", email="test2@example.com")
        assert "already exists" in str(exc_info.value)

    def test_create_player_duplicate_email(self) -> None:
        """Test creating player with duplicate email."""
        # Arrange
        self.service.create_player(username="player1", email="test@example.com")

        # Act & Assert
        with pytest.raises(ConflictException) as exc_info:
            self.service.create_player(username="player2", email="test@example.com")
        assert "already exists" in str(exc_info.value)

    def test_get_player_success(self) -> None:
        """Test successful player retrieval."""
        # Arrange
        created_player = self.service.create_player(
            username="testplayer", email="test@example.com"
        )

        # Act
        retrieved_player = self.service.get_player(created_player.player_id)

        # Assert
        assert retrieved_player.player_id == created_player.player_id
        assert retrieved_player.username == "testplayer"

    def test_get_player_not_found(self) -> None:
        """Test getting non-existent player."""
        # Arrange
        # Act & Assert
        with pytest.raises(NotFoundException) as exc_info:
            self.service.get_player("plr_nonexistent")
        assert "not found" in str(exc_info.value)

    def test_update_player_success(self) -> None:
        """Test successful player update."""
        # Arrange
        player = self.service.create_player(
            username="testplayer", email="test@example.com"
        )

        update_request = UpdatePlayerRequest(
            display_name="Updated Name", status=PlayerStatus.SUSPENDED
        )

        # Act
        updated_player = self.service.update_player(player.player_id, update_request)

        # Assert
        assert updated_player.display_name == "Updated Name"
        assert updated_player.status == PlayerStatus.SUSPENDED

    def test_update_player_email_conflict(self) -> None:
        """Test updating player with conflicting email."""
        # Arrange
        player1 = self.service.create_player(username="player1", email="p1@example.com")
        self.service.create_player(username="player2", email="p2@example.com")

        update_request = UpdatePlayerRequest(email="p2@example.com")

        # Act & Assert
        with pytest.raises(ConflictException) as exc_info:
            self.service.update_player(player1.player_id, update_request)
        assert "already exists" in str(exc_info.value)

    def test_delete_player_success(self) -> None:
        """Test successful player deletion."""
        # Arrange
        player = self.service.create_player(
            username="testplayer", email="test@example.com"
        )

        # Act
        self.service.delete_player(player.player_id)

        # Assert
        with pytest.raises(NotFoundException):
            self.service.get_player(player.player_id)

    def test_delete_player_not_found(self) -> None:
        """Test deleting non-existent player."""
        # Arrange
        # Act & Assert
        with pytest.raises(NotFoundException):
            self.service.delete_player("plr_nonexistent")

    def test_list_players(self) -> None:
        """Test listing all players."""
        # Arrange
        self.service.create_player(username="player1", email="p1@example.com")
        self.service.create_player(username="player2", email="p2@example.com")

        # Act
        players = self.service.list_players()

        # Assert
        assert len(players) == 2
        usernames = {p.username for p in players}
        assert "player1" in usernames
        assert "player2" in usernames

    def test_get_player_stats_success(self) -> None:
        """Test successful player stats retrieval."""
        # Arrange
        player = self.service.create_player(
            username="testplayer", email="test@example.com"
        )

        # Act
        stats = self.service.get_player_stats(player.player_id)

        # Assert
        assert stats.player_id == player.player_id
        assert stats.total_games == 0
        assert stats.wins == 0

    def test_get_player_stats_not_found(self) -> None:
        """Test getting stats for non-existent player."""
        # Arrange
        # Act & Assert
        with pytest.raises(NotFoundException):
            self.service.get_player_stats("plr_nonexistent")
