# IDP API Lambda

Identity Provider API Lambda function for authentication and token management in the PSN Partner Emulator Service.

## Overview

The IDP API provides authentication services including:

- User authentication with username/password
- Access token generation and validation
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
# Install dependencies and create virtual environment
uv sync

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Run tests using the consolidated test script (recommended)
uv run python scripts/test.py --service idp_api --coverage --html

# Run tests directly with pytest
uv run pytest services/idp_api/tests/

# Run only unit tests
uv run python scripts/test.py --service idp_api --type unit --verbose

# Run only integration tests
uv run python scripts/test.py --service idp_api --type integration --verbose

# Run tests in parallel
uv run python scripts/test.py --service idp_api --parallel --workers 4

# Run with coverage and HTML report
uv run python scripts/test.py --service idp_api --coverage --html --html-dir coverage_report
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

The IDP API dependencies are defined in `pyproject.toml`:

```toml
dependencies = [
    "pydantic[email]>=2.10.0",  # Request/response validation with email support
    "aws-lambda-powertools>=3.4.0",  # Logging and utilities
]
```

**Key Dependencies:**
- **aws-lambda-powertools**: Logging and utilities (shared across services)
- **pydantic[email]**: Request/response validation with email validation support
- **boto3**: AWS SDK (for future integrations)

**Version Management:**
- Dependencies are version-pinned in `pyproject.toml`
- ZIP build script reads exact versions for consistent deployments
- Email validation extras are included for user email validation

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
# Using consolidated test script (recommended)
uv run python scripts/test.py --service idp_api --verbose

# All tests with pytest (direct)
uv run pytest services/idp_api/tests/ -v

# Unit tests only
uv run python scripts/test.py --service idp_api --type unit --verbose

# Integration tests only
uv run python scripts/test.py --service idp_api --type integration --verbose
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
- Access token expiration (1 hour access tokens)
- Token type validation (access vs refresh tokens)
- Input validation with Pydantic models
- Secure token generation using secrets.token_urlsafe()

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

## Docker Deployment

This Lambda function is deployed as a Docker container with per-Lambda independence.

### Building Docker Images

```bash
# Build this Lambda specifically
uv run python scripts/build.py --service idp_api --tag v1.0.0

# Build all Lambdas
uv run python scripts/build.py --service all --tag v1.0.0

# Build without cache (clean build)
uv run python scripts/build.py --service idp_api --no-cache --tag v1.0.0

# Build and push to ECR
uv run python scripts/build.py --service idp_api --tag v1.0.0 --push --ecr-repo-map '{"idp_api": "123456789012.dkr.ecr.us-east-1.amazonaws.com/fips-psn-idp-api"}'
```

### Local Docker Testing

```bash
# Build the image locally
uv run python scripts/build.py --service idp_api --tag dev

# Run locally
docker run -p 9000:8080 fips-psn-idp-api:dev

# Test with curl
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{"body": "{\"username\":\"testuser\",\"password\":\"password123\"}"}'
```

### Docker Architecture

- **Multi-stage build**: Minimal final image size with only runtime dependencies
- **Base image**: `public.ecr.aws/lambda/python:3.13`
- **Package manager**: `uv` for fast dependency resolution
- **Common library**: Installed from local path during build
- **Environment variables**: `POWERTOOLS_SERVICE_NAME=idp-api`

## Deployment

Deployed via Terraform configuration in `infra/terraform/`:

- Lambda function definition in `lambda.tf` (container-based)
- API Gateway routing in `api_gateway.tf`
- ECR repositories in `ecr.tf`
- IAM permissions in `lambda.tf`

### Deploy Script

```bash
# Build and deploy all Lambdas
uv run python scripts/deploy.py --tag v1.0.0 --environment dev

# Deploy specific Lambda only
uv run python scripts/deploy.py --tag v1.0.0 --services idp_api --environment dev

# Deploy without building (use existing local images)
uv run python scripts/deploy.py --tag v1.0.0 --no-build --environment dev
```

## Future Enhancements

- [ ] Integration with real user database
- [ ] Multi-factor authentication support
- [ ] OAuth 2.0 flows
- [ ] Rate limiting and throttling
- [ ] Advanced token management
- [ ] Password policy enforcement