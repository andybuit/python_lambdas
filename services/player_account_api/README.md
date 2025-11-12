# Player Account API Lambda

Player Account API Lambda function for player account management and statistics tracking in the PSN Partner Emulator Service.

## Overview

The Player Account API provides player management services including:

- Player account creation and management
- Player profile updates and deletion
- Player statistics tracking
- Player listing and search

## API Endpoints

### POST /players

Create a new player account.

**Request:**
```json
{
  "username": "player1",
  "email": "player1@example.com",
  "display_name": "Player One"
}
```

**Response:**
```json
{
  "player_id": "plr_123456",
  "username": "player1",
  "email": "player1@example.com",
  "display_name": "Player One",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### GET /players

List all player accounts.

**Response:**
```json
{
  "players": [
    {
      "player_id": "plr_123456",
      "username": "player1",
      "email": "player1@example.com",
      "display_name": "Player One",
      "status": "active"
    }
  ],
  "count": 1,
  "total": 1
}
```

### GET /players/{player_id}

Get specific player account.

**Response:**
```json
{
  "player_id": "plr_123456",
  "username": "player1",
  "email": "player1@example.com",
  "display_name": "Player One",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### PUT /players/{player_id}

Update player account.

**Request:**
```json
{
  "display_name": "Updated Name",
  "status": "active",
  "email": "newemail@example.com"
}
```

**Response:**
```json
{
  "player_id": "plr_123456",
  "username": "player1",
  "email": "newemail@example.com",
  "display_name": "Updated Name",
  "status": "active",
  "updated_at": "2024-01-01T01:00:00Z"
}
```

### DELETE /players/{player_id}

Delete player account.

**Response:** 204 No Content

### GET /players/{player_id}/stats

Get player statistics.

**Response:**
```json
{
  "player_id": "plr_123456",
  "total_games": 42,
  "wins": 28,
  "losses": 14,
  "win_rate": 0.667,
  "last_played": "2024-01-01T00:00:00Z",
  "achievements_unlocked": 15
}
```

## Architecture

```
┌─────────────────┐
│  API Gateway    │
│  (HTTP API)     │
└────────┬────────┘
         │ POST /players
         │ GET /players
         │ GET /players/{id}
         │ PUT /players/{id}
         │ DELETE /players/{id}
         │ GET /players/{id}/stats
         ▼
┌─────────────────┐
│ Player Account  │
│ API Lambda      │
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
services/player_account_api/
├── handler.py         # Lambda handler with API Gateway routing
├── service.py         # Player management business logic
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
uv run python scripts/test.py --service player_account_api --coverage --html

# Run tests directly with pytest
uv run pytest services/player_account_api/tests/

# Run only unit tests
uv run python scripts/test.py --service player_account_api --type unit --verbose

# Run only integration tests
uv run python scripts/test.py --service player_account_api --type integration --verbose

# Run tests in parallel
uv run python scripts/test.py --service player_account_api --parallel --workers 4

# Run with coverage and HTML report
uv run python scripts/test.py --service player_account_api --coverage --html --html-dir coverage_report
```

### Local Testing with Mock Events

Create a test event file `test_create_player.json`:

```json
{
  "httpMethod": "POST",
  "path": "/players",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": "{\"username\":\"testplayer\",\"email\":\"test@example.com\",\"display_name\":\"Test Player\"}"
}
```

Run handler locally:

```python
from services.player_account_api.handler import lambda_handler
import json

with open('test_create_player.json') as f:
    event = json.load(f)

response = lambda_handler(event, None)
print(json.dumps(response, indent=2))
```

### Debugging in VS Code

1. Set breakpoints in `handler.py` or `service.py`
2. Press `F5` and select "Debug: Player Account API Lambda"
3. Use the VS Code debugger to step through code

## Key Components

### handler.py

- **lambda_handler**: Main entry point for API Gateway events
- **handle_create_player**: Creates new player accounts
- **handle_get_player**: Retrieves player information
- **handle_update_player**: Updates player data
- **handle_delete_player**: Deletes player accounts
- **handle_list_players**: Lists all players
- **handle_get_player_stats**: Retrieves player statistics
- **Response helpers**: Create standardized API responses

### service.py

- **PlayerAccountService**: Core player management logic
- **Player validation**: Username/email uniqueness checks
- **Statistics tracking**: Game statistics management
- **Player lifecycle**: CRUD operations

### models.py

- **PlayerAccount**: Player account data model
- **CreatePlayerRequest**: Player creation request model
- **UpdatePlayerRequest**: Player update request model
- **PlayerStats**: Player statistics model
- **PlayerStatus**: Player status enumeration

## Dependencies

The Player Account API dependencies are defined in `pyproject.toml`:

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
- **typing**: Type hints support

**Version Management:**
- Dependencies are version-pinned in `pyproject.toml`
- ZIP build script reads exact versions for consistent deployments
- Email validation extras are included for player email validation

## Environment Variables

- `ENVIRONMENT`: Deployment environment (dev/staging/prod)
- `LOG_LEVEL`: Logging level (DEBUG/INFO/WARN/ERROR)
- `POWERTOOLS_SERVICE_NAME`: Service name for logging

## Testing

### Unit Tests

- **test_handler.py**: Tests API Gateway request handling
- **test_service.py**: Tests player management business logic

### Integration Tests

- **test_integration.py**: Tests complete player lifecycle flows

### Running Tests

```bash
# Using consolidated test script (recommended)
uv run python scripts/test.py --service player_account_api --verbose

# All tests with pytest (direct)
uv run pytest services/player_account_api/tests/ -v

# Unit tests only
uv run python scripts/test.py --service player_account_api --type unit --verbose

# Integration tests only
uv run python scripts/test.py --service player_account_api --type integration --verbose
```

## Error Handling

The API uses standardized error responses:

```json
{
  "error": "ConflictException",
  "message": "Username 'player1' already exists",
  "details": {
    "error_code": "DUPLICATE_USERNAME",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Common Errors

- **ConflictException**: Duplicate username or email
- **NotFoundException**: Player not found
- **ValidationException**: Malformed request data

## Player Status

Players can have the following statuses:

- **active**: Player is active and can play games
- **suspended**: Player is temporarily suspended
- **inactive**: Player account is inactive

## Data Model

### PlayerAccount

```python
class PlayerAccount:
    player_id: str        # Unique identifier (plr_xxxxxx)
    username: str         # Unique username
    email: str           # Unique email address
    display_name: str    # Display name (optional)
    status: PlayerStatus # Player status
    created_at: datetime # Account creation time
    updated_at: datetime # Last update time
```

### PlayerStats

```python
class PlayerStats:
    player_id: str              # Player identifier
    total_games: int           # Total games played
    wins: int                  # Number of wins
    losses: int                # Number of losses
    win_rate: float            # Win percentage
    last_played: datetime      # Last game time
    achievements_unlocked: int # Achievement count
```

## Security Considerations

- Input validation with Pydantic models
- Username and email uniqueness enforcement
- Email format validation
- SQL injection prevention (when using databases)

## Monitoring

### Logging

Uses AWS Lambda Powertools for structured logging:

```python
from libs.logger import get_logger

logger = get_logger(__name__)
logger.info("Player created", extra={"player_id": player_id, "username": username})
```

### Metrics

Track player management metrics:

- Player creations
- Player updates
- Player deletions
- Player statistics requests

## Docker Deployment

This Lambda function is deployed as a Docker container with per-Lambda independence.

### Building Docker Images

```bash
# Build this Lambda specifically
uv run python scripts/build.py --service player_account_api --tag v1.0.0

# Build all Lambdas
uv run python scripts/build.py --service all --tag v1.0.0

# Build without cache (clean build)
uv run python scripts/build.py --service player_account_api --no-cache --tag v1.0.0

# Build and push to ECR
uv run python scripts/build.py --service player_account_api --tag v1.0.0 --push --ecr-repo-map '{"player_account_api": "123456789012.dkr.ecr.us-east-1.amazonaws.com/fips-psn-player-account-api"}'
```

### Local Docker Testing

```bash
# Build the image locally
uv run python scripts/build.py --service player_account_api --tag dev

# Run locally
docker run -p 9000:8080 fips-psn-player-account-api:dev

# Test with curl
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{"body": "{\"username\":\"testplayer\",\"email\":\"test@example.com\",\"display_name\":\"Test Player\"}"}'
```

### Docker Architecture

- **Multi-stage build**: Minimal final image size with only runtime dependencies
- **Base image**: `public.ecr.aws/lambda/python:3.13`
- **Package manager**: `uv` for fast dependency resolution
- **Common library**: Installed from local path during build
- **Environment variables**: `POWERTOOLS_SERVICE_NAME=player-account-api`

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
uv run python scripts/deploy.py --tag v1.0.0 --services player_account_api --environment dev

# Deploy without building (use existing local images)
uv run python scripts/deploy.py --tag v1.0.0 --no-build --environment dev
```

## Future Enhancements

- [ ] Integration with DynamoDB for persistence
- [ ] Player search and filtering
- [ ] Player avatar management
- [ ] Player relationships and friends
- [ ] Advanced statistics and analytics
- [ ] Player achievement system
- [ ] Player preferences and settings
- [ ] Bulk player operations
- [ ] Player export/import functionality