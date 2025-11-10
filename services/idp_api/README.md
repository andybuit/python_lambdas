# IDP API Lambda

Identity Provider API Lambda function for authentication and token management in the PSN Partner Emulator Service.

## Overview

The IDP API provides authentication services including:

- User authentication with username/password
- JWT access token generation and validation
- Token refresh functionality
- User information retrieval

## API Endpoints

### POST /auth/token

Authenticate user and receive access token.

**Request:**
```json
{
  "username": "testuser",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### GET /auth/userinfo

Get authenticated user information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "user_id": "usr_001",
  "username": "testuser",
  "email": "testuser@example.com",
  "is_active": true
}
```

### POST /auth/refresh

Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "..."
}
```

**Response:**
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

## Architecture

```
┌─────────────────┐
│  API Gateway    │
│  (HTTP API)     │
└────────┬────────┘
         │ POST /auth/token
         │ GET /auth/userinfo
         │ POST /auth/refresh
         ▼
┌─────────────────┐
│   IDP API       │
│   Lambda        │
│                 │
│ ┌─────────────┐ │
│ │  handler.py │ │ ← API Gateway routing
│ └─────────────┘ │
│ ┌─────────────┐ │
│ │  service.py │ │ ← Business logic
│ └─────────────┘ │
│ ┌─────────────┐ │
│ │  models.py  │ │ ← Pydantic models
│ └─────────────┘ │
└─────────────────┘
```

## Files Structure

```
services/idp_api/
├── handler.py         # Lambda handler with API Gateway routing
├── service.py         # Authentication business logic
├── models.py          # Pydantic request/response models
├── README.md          # This file
└── tests/
    ├── unit/          # Unit tests
    │   ├── test_handler.py    # Handler unit tests
    │   └── test_service.py    # Service unit tests
    └── integration/   # Integration tests
        └── test_integration.py # End-to-end tests
```

## Local Development

### Running Tests

```bash
# Run all IDP API tests
uv run pytest services/idp_api/tests/

# Run only unit tests
uv run pytest services/idp_api/tests/unit/

# Run only integration tests
uv run pytest services/idp_api/tests/integration/

# Run with coverage
uv run pytest services/idp_api/tests/ --cov=services.idp_api
```

### Local Testing with Mock Events

Create a test event file `test_event.json`:

```json
{
  "httpMethod": "POST",
  "path": "/auth/token",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": "{\"username\":\"testuser\",\"password\":\"password123\"}"
}
```

Run handler locally:

```python
from services.idp_api.handler import lambda_handler
import json

with open('test_event.json') as f:
    event = json.load(f)

response = lambda_handler(event, None)
print(json.dumps(response, indent=2))
```

### Debugging in VS Code

1. Set breakpoints in `handler.py` or `service.py`
2. Press `F5` and select "Debug: IDP API Lambda"
3. Use the VS Code debugger to step through code

## Key Components

### handler.py

- **lambda_handler**: Main entry point for API Gateway events
- **handle_authentication**: Processes authentication requests
- **handle_userinfo**: Retrieves user information
- **handle_refresh_token**: Refreshes access tokens
- **Response helpers**: Create standardized API responses

### service.py

- **IDPService**: Core authentication logic
- **Token management**: JWT generation and validation
- **User authentication**: Credential verification
- **Token refresh**: Access token renewal

### models.py

- **TokenResponse**: Authentication response model
- **UserInfo**: User information model
- **AuthenticationRequest**: Authentication request model

## Dependencies

- **aws-lambda-powertools**: Logging and utilities
- **pydantic**: Request/response validation
- **boto3**: AWS SDK (for future integrations)
- **jwt**: JSON Web Token handling

## Environment Variables

- `ENVIRONMENT`: Deployment environment (dev/staging/prod)
- `LOG_LEVEL`: Logging level (DEBUG/INFO/WARN/ERROR)
- `POWERTOOLS_SERVICE_NAME`: Service name for logging

## Testing

### Unit Tests

- **test_handler.py**: Tests API Gateway request handling
- **test_service.py**: Tests authentication business logic

### Integration Tests

- **test_integration.py**: Tests complete authentication flows

### Running Tests

```bash
# All tests
uv run pytest services/idp_api/tests/ -v

# Unit tests only
uv run pytest services/idp_api/tests/unit/ -v

# Integration tests only
uv run pytest services/idp_api/tests/integration/ -v -m integration
```

## Error Handling

The API uses standardized error responses:

```json
{
  "error": "AuthenticationException",
  "message": "Invalid username or password",
  "details": {
    "error_code": "INVALID_CREDENTIALS",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Common Errors

- **AuthenticationException**: Invalid credentials or expired tokens
- **ValidationException**: Malformed request data
- **NotFoundException**: User not found

## Security Considerations

- Password validation against mock user database
- JWT token expiration (1 hour access tokens)
- Token type validation (access vs refresh tokens)
- Input validation with Pydantic models

## Monitoring

### Logging

Uses AWS Lambda Powertools for structured logging:

```python
from libs.logger import get_logger

logger = get_logger(__name__)
logger.info("Authentication attempt", extra={"username": username})
```

### Metrics

Track authentication metrics:

- Successful authentications
- Failed authentication attempts
- Token refresh operations
- User information requests

## Deployment

Deployed via Terraform configuration in `infra/terraform/`:

- Lambda function definition in `lambda.tf`
- API Gateway routing in `api_gateway.tf`
- IAM permissions in `lambda.tf`

## Future Enhancements

- [ ] Integration with real user database
- [ ] Multi-factor authentication support
- [ ] OAuth 2.0 flows
- [ ] Rate limiting and throttling
- [ ] Advanced token management
- [ ] Password policy enforcement