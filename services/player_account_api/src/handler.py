"""Lambda handler for Player Account API."""

import json
from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from libs.common.src.exceptions import PSNEmulatorException, ValidationException
from libs.common.src.logger import get_logger
from libs.common.src.models import ErrorResponse
from pydantic import ValidationError

# Try absolute imports first (for Docker), then relative imports (for local testing)
try:
    from models import (
        CreatePlayerRequest,
        UpdatePlayerRequest,
    )
    from service import PlayerAccountService
except ImportError:
    from .models import (
        CreatePlayerRequest,
        UpdatePlayerRequest,
    )
    from .service import PlayerAccountService

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], _context: LambdaContext) -> dict[str, Any]:
    """
    AWS Lambda handler for Player Account API requests.

    This handler processes player account operations including creation,
    retrieval, updates, and deletion of player accounts.

    Args:
        event: Lambda event dict containing API Gateway request data
        context: Lambda context object with runtime information

    Returns:
        dict: API Gateway response with status code, headers, and body

    Raises:
        ValidationException: When request validation fails
        PSNEmulatorException: For other service-level errors
    """
    logger.info(
        "Player Account API request received", extra={"path": event.get("path")}
    )

    try:
        http_method = event.get("httpMethod", "")
        path = event.get("path", "")
        path_params = event.get("pathParameters") or {}
        body = json.loads(event.get("body", "{}")) if event.get("body") else {}

        # Route to appropriate handler - check more specific paths first
        if http_method == "POST" and path.endswith("/players"):
            return handle_create_player(body)
        elif http_method == "GET" and path.endswith("/players"):
            return handle_list_players()
        elif http_method == "GET" and "/players/" in path and path.endswith("/stats"):
            player_id = path_params.get("player_id")
            if not player_id:
                return create_error_response(
                    400, "BAD_REQUEST", "player_id is required"
                )
            return handle_get_player_stats(player_id)
        elif http_method == "GET" and "/players/" in path:
            player_id = path_params.get("player_id")
            if not player_id:
                return create_error_response(
                    400, "BAD_REQUEST", "player_id is required"
                )
            return handle_get_player(player_id)
        elif http_method == "PUT" and "/players/" in path:
            player_id = path_params.get("player_id")
            if not player_id:
                return create_error_response(
                    400, "BAD_REQUEST", "player_id is required"
                )
            return handle_update_player(player_id, body)
        elif http_method == "DELETE" and "/players/" in path:
            player_id = path_params.get("player_id")
            if not player_id:
                return create_error_response(
                    400, "BAD_REQUEST", "player_id is required"
                )
            return handle_delete_player(player_id)
        else:
            return create_error_response(
                404, "NOT_FOUND", f"Endpoint not found: {http_method} {path}"
            )

    except ValidationException as e:
        logger.warning("Validation error", extra={"error": str(e)})
        return create_error_response(e.status_code, "VALIDATION_ERROR", e.message)

    except PSNEmulatorException as e:
        logger.error("Service error", extra={"error": str(e)})
        return create_error_response(e.status_code, "SERVICE_ERROR", e.message)

    except Exception as e:
        logger.exception("Unexpected error", extra={"error": str(e)})
        return create_error_response(
            500, "INTERNAL_ERROR", "An unexpected error occurred"
        )


def handle_create_player(body: dict[str, Any]) -> dict[str, Any]:
    """
    Handle create player request.

    Args:
        body: Request body with player data

    Returns:
        dict: API Gateway response with created player
    """
    try:
        request = CreatePlayerRequest(**body)
        service = PlayerAccountService()
        player = service.create_player(
            username=request.username,
            email=request.email,
            display_name=request.display_name,
        )
        return create_success_response(201, player.model_dump_json())

    except ValidationError as e:
        raise ValidationException(str(e)) from e


def handle_get_player(player_id: str) -> dict[str, Any]:
    """
    Handle get player request.

    Args:
        player_id: Player identifier

    Returns:
        dict: API Gateway response with player data
    """
    service = PlayerAccountService()
    player = service.get_player(player_id)
    return create_success_response(200, player.model_dump_json())


def handle_update_player(player_id: str, body: dict[str, Any]) -> dict[str, Any]:
    """
    Handle update player request.

    Args:
        player_id: Player identifier
        body: Request body with update data

    Returns:
        dict: API Gateway response with updated player
    """
    try:
        request = UpdatePlayerRequest(**body)
        service = PlayerAccountService()
        player = service.update_player(player_id, request)
        return create_success_response(200, player.model_dump_json())

    except ValidationError as e:
        raise ValidationException(str(e)) from e


def handle_delete_player(player_id: str) -> dict[str, Any]:
    """
    Handle delete player request.

    Args:
        player_id: Player identifier

    Returns:
        dict: API Gateway response confirming deletion
    """
    service = PlayerAccountService()
    service.delete_player(player_id)
    return create_success_response(204, {})


def handle_list_players() -> dict[str, Any]:
    """
    Handle list players request.

    Returns:
        dict: API Gateway response with list of players
    """
    service = PlayerAccountService()
    players = service.list_players()
    players_data = {
        "players": [json.loads(p.model_dump_json()) for p in players],
        "count": len(players),
    }
    return create_success_response(200, players_data)


def handle_get_player_stats(player_id: str) -> dict[str, Any]:
    """
    Handle get player stats request.

    Args:
        player_id: Player identifier

    Returns:
        dict: API Gateway response with player statistics
    """
    service = PlayerAccountService()
    stats = service.get_player_stats(player_id)
    return create_success_response(200, stats.model_dump_json())


def create_success_response(
    status_code: int, data: dict[str, Any] | str
) -> dict[str, Any]:
    """
    Create a successful API Gateway response.

    Args:
        status_code: HTTP status code
        data: Response data (dict or JSON string)

    Returns:
        dict: Formatted API Gateway response
    """
    body = data if isinstance(data, str) else (json.dumps(data) if data else "")
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": body,
    }


def create_error_response(
    status_code: int, error_type: str, message: str
) -> dict[str, Any]:
    """
    Create an error API Gateway response.

    Args:
        status_code: HTTP status code
        error_type: Error type identifier
        message: Error message

    Returns:
        dict: Formatted API Gateway error response
    """
    error_response = ErrorResponse(error=error_type, message=message)

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": error_response.model_dump_json(),
    }
