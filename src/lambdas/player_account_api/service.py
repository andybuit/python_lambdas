"""Business logic for Player Account API."""

import secrets
from datetime import datetime

from src.lambdas.player_account_api.models import (
    PlayerAccount,
    PlayerStats,
    PlayerStatus,
    UpdatePlayerRequest,
)
from src.shared.exceptions import ConflictException, NotFoundException
from src.shared.logger import get_logger

logger = get_logger(__name__)


class PlayerAccountService:
    """Service class for Player Account operations."""

    # In-memory storage for demo purposes - replace with DynamoDB in production
    _players: dict[str, PlayerAccount] = {}
    _stats: dict[str, PlayerStats] = {}

    def create_player(
        self, username: str, email: str, display_name: str | None = None
    ) -> PlayerAccount:
        """
        Create a new player account.

        Args:
            username: Player username
            email: Player email address
            display_name: Optional display name

        Returns:
            PlayerAccount: Created player account

        Raises:
            ConflictException: When username or email already exists
        """
        logger.info("Creating player account", extra={"username": username})

        # Check for existing username
        for player in self._players.values():
            if player.username == username:
                raise ConflictException(f"Username '{username}' already exists")
            if player.email == email:
                raise ConflictException(f"Email '{email}' already exists")

        # Generate player ID
        player_id = f"plr_{secrets.token_hex(8)}"

        # Create player account
        player = PlayerAccount(
            player_id=player_id,
            username=username,
            email=email,
            display_name=display_name or username,
            status=PlayerStatus.ACTIVE,
        )

        # Initialize player stats
        stats = PlayerStats(player_id=player_id)

        # Store in memory
        self._players[player_id] = player
        self._stats[player_id] = stats

        logger.info(
            "Player account created",
            extra={"player_id": player_id, "username": username},
        )

        return player

    def get_player(self, player_id: str) -> PlayerAccount:
        """
        Get player account by ID.

        Args:
            player_id: Player identifier

        Returns:
            PlayerAccount: Player account data

        Raises:
            NotFoundException: When player not found
        """
        player = self._players.get(player_id)
        if not player:
            raise NotFoundException(f"Player with ID '{player_id}' not found")

        return player

    def update_player(
        self, player_id: str, update_request: UpdatePlayerRequest
    ) -> PlayerAccount:
        """
        Update player account.

        Args:
            player_id: Player identifier
            update_request: Update request with new values

        Returns:
            PlayerAccount: Updated player account

        Raises:
            NotFoundException: When player not found
            ConflictException: When email already exists for another player
        """
        logger.info("Updating player account", extra={"player_id": player_id})

        player = self.get_player(player_id)

        # Check for email conflict
        if update_request.email:
            for pid, p in self._players.items():
                if pid != player_id and p.email == update_request.email:
                    raise ConflictException(
                        f"Email '{update_request.email}' already exists"
                    )

        # Update fields
        if update_request.display_name is not None:
            player.display_name = update_request.display_name
        if update_request.email is not None:
            player.email = update_request.email
        if update_request.status is not None:
            player.status = update_request.status

        player.updated_at = datetime.utcnow()

        logger.info("Player account updated", extra={"player_id": player_id})

        return player

    def delete_player(self, player_id: str) -> None:
        """
        Delete player account.

        Args:
            player_id: Player identifier

        Raises:
            NotFoundException: When player not found
        """
        logger.info("Deleting player account", extra={"player_id": player_id})

        if player_id not in self._players:
            raise NotFoundException(f"Player with ID '{player_id}' not found")

        # Remove player and stats
        del self._players[player_id]
        if player_id in self._stats:
            del self._stats[player_id]

        logger.info("Player account deleted", extra={"player_id": player_id})

    def list_players(self) -> list[PlayerAccount]:
        """
        List all player accounts.

        Returns:
            list[PlayerAccount]: List of all players
        """
        return list(self._players.values())

    def get_player_stats(self, player_id: str) -> PlayerStats:
        """
        Get player statistics.

        Args:
            player_id: Player identifier

        Returns:
            PlayerStats: Player statistics

        Raises:
            NotFoundException: When player or stats not found
        """
        # Verify player exists
        self.get_player(player_id)

        stats = self._stats.get(player_id)
        if not stats:
            raise NotFoundException(f"Stats for player '{player_id}' not found")

        return stats
