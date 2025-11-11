"""Lambda handler for IDP API."""

import json
from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import ValidationError

from libs.common.src.exceptions import PSNEmulatorException, ValidationException
from libs.common.src.logger import get_logger
from libs.common.src.models import ErrorResponse
from .models import AuthenticationRequest, TokenResponse
from .service import IDPService

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    AWS Lambda handler for IDP API requests.

    This handler processes authentication and identity provider requests,
    including user login, token issuance, and token refresh operations.

    Args:
        event: Lambda event dict containing API Gateway request data
        context: Lambda context object with runtime information

    Returns:
        dict: API Gateway response with status code, headers, and body

    Raises:
        ValidationException: When request validation fails
        PSNEmulatorException: For other service-level errors
    """
    logger.info("IDP API request received", extra={"path": event.get("path")})

    try:
        # Parse request body
        body_str = event.get("body", "{}") or "{}"
        body = json.loads(body_str)
        http_method = event.get("httpMethod", "")
        path = event.get("path", "")

        # Route to appropriate handler
        if http_method == "POST" and path.endswith("/auth/token"):
            return handle_authentication(body)
        elif http_method == "GET" and path.endswith("/auth/userinfo"):
            return handle_userinfo(event)
        elif http_method == "POST" and path.endswith("/auth/refresh"):
            return handle_token_refresh(body)
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


def handle_authentication(body: dict[str, Any]) -> dict[str, Any]:
    """
    Handle user authentication request.

    Args:
        body: Request body containing authentication credentials

    Returns:
        dict: API Gateway response with authentication token
    """
    try:
        # Validate request
        auth_request = AuthenticationRequest(**body)

        # Process authentication
        service = IDPService()
        token_response = service.authenticate(
            auth_request.username, auth_request.password
        )

        return create_success_response(200, token_response.model_dump_json())

    except ValidationError as e:
        raise ValidationException(str(e)) from e


def handle_userinfo(event: dict[str, Any]) -> dict[str, Any]:
    """
    Handle user info request.

    Args:
        event: Lambda event with authorization header

    Returns:
        dict: API Gateway response with user information
    """
    # Extract token from Authorization header
    headers = event.get("headers", {})
    auth_header = headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        raise ValidationException("Invalid or missing Authorization header")

    token = auth_header.replace("Bearer ", "")

    # Get user info
    service = IDPService()
    user_info = service.get_user_info(token)

    return create_success_response(200, user_info.model_dump_json())


def handle_token_refresh(body: dict[str, Any]) -> dict[str, Any]:
    """
    Handle token refresh request.

    Args:
        body: Request body containing refresh token

    Returns:
        dict: API Gateway response with new access token
    """
    refresh_token = body.get("refresh_token")
    if not refresh_token:
        raise ValidationException("refresh_token is required")

    service = IDPService()
    token_response = service.refresh_token(refresh_token)

    return create_success_response(200, token_response.model_dump_json())


def create_success_response(status_code: int, data: dict[str, Any] | str) -> dict[str, Any]:
    """
    Create a successful API Gateway response.

    Args:
        status_code: HTTP status code
        data: Response data (dict or JSON string)

    Returns:
        dict: Formatted API Gateway response
    """
    body = data if isinstance(data, str) else json.dumps(data)
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
