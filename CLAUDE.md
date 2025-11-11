# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **PSN Partner Emulator Service** (`fips-psn-emulator-service`) - a serverless AWS Lambda application that emulates partner API environments for early integration, validation, and QA of PSN software without requiring access to partner production systems.

### Architecture

The project follows a **serverless microservices pattern** with:
- **API Gateway HTTP API**: Single entry point that routes to different Lambda functions
- **Two Lambda Functions**:
  - `idp_api` - Identity Provider API for authentication and token management
  - `player_account_api` - Player account management and statistics
- **Shared Libraries**: Common utilities, models, exceptions, and logging in `libs/common/src/`
- **Terraform Infrastructure**: Infrastructure as Code for AWS deployment in `infra/terraform/`

### Key Technologies

- **Python 3.13+** with **uv** package manager
- **AWS Lambda Powertools v3.4.0+** for structured logging and utilities
- **Pydantic v2.10.0+** for request/response validation
- **pytest v8.3.0+** for testing with comprehensive coverage
- **Terraform v1.5.0+** for infrastructure deployment
- **boto3 v1.35.0+** for AWS SDK interactions

## Project Structure

```
python_lambdas/
├── .claude/                      # Claude Code configuration
├── .vscode/                      # VS Code debugging configurations
│   ├── launch.json               # Debug configurations for Lambdas
│   ├── settings.json             # VS Code settings
│   ├── extensions.json           # Recommended extensions
│   └── tasks.json                # Build tasks
├── libs/                         # Shared libraries across Lambdas
│   └── common/                   # Common utilities
│       ├── __init__.py
│       └── src/                  # Source code (NEW STRUCTURE)
│           ├── __init__.py
│           ├── exceptions.py     # Custom exception hierarchy
│           ├── logger.py         # AWS Lambda Powertools logger configuration
│           └── models.py         # Common response models (APIResponse, ErrorResponse)
├── services/                     # Lambda functions (services)
│   ├── idp_api/                  # Identity Provider API Lambda
│   │   ├── src/                  # Source code (NEW STRUCTURE)
│   │   │   ├── __init__.py
│   │   │   ├── handler.py        # Lambda entry point with routing
│   │   │   ├── service.py        # Business logic
│   │   │   └── models.py         # Pydantic request/response models
│   │   └── tests/                # Unit and integration tests
│   │       ├── integration/
│   │       │   └── test_integration.py
│   │       └── unit/
│   │           ├── test_handler.py
│   │           └── test_service.py
│   └── player_account_api/       # Player Account API Lambda
│       ├── src/                  # Source code (NEW STRUCTURE)
│       │   ├── __init__.py
│       │   ├── handler.py
│       │   ├── service.py
│       │   └── models.py
│       └── tests/                # Unit and integration tests
│           ├── integration/
│           │   └── test_integration.py
│           └── unit/
│               ├── test_handler.py
│               └── test_service.py
├── tests/                        # End-to-end tests
│   └── e2e/
│       ├── conftest.py           # Pytest fixtures for E2E tests
│       └── __init__.py
├── infra/                        # Infrastructure as Code
│   └── terraform/                # Terraform configurations
│       ├── main.tf               # Provider and backend configuration
│       ├── lambda.tf             # Lambda function definitions
│       ├── api_gateway.tf        # API Gateway routing
│       ├── variables.tf          # Input variables
│       └── outputs.tf            # Output values
├── pyproject.toml                # Project configuration and dependencies
├── .pre-commit-config.yaml       # Pre-commit hooks configuration
├── .coverage                     # Coverage data file
├── coverage.xml                  # Coverage report in XML format
├── htmlcov/                      # HTML coverage report directory
├── uv.lock                       # Lock file for uv package manager
├── README.md                     # Project documentation
├── SETUP_CHECKLIST.md            # Setup checklist for developers
└── CLAUDE.md                     # This file - Claude Code guidance
```

## Code Structure Changes (Recent Updates)

### 🆕 NEW: src/ Directory Structure
All Python source code has been reorganized into `src/` directories for better separation of concerns:

- **Lambda Functions**: Each Lambda now has its code in `services/{name}/src/`
- **Shared Libraries**: Common code is in `libs/common/src/`
- **Benefits**: Cleaner deployment, better import organization, and separation from tests

### Import Path Updates
- **Within Lambda files**: Use relative imports (`.models`, `.service`)
- **Cross-module imports**:
  - Libraries: `from libs.common.src.exceptions import ...`
  - Tests: `from services.idp_api.src.handler import ...`

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install
```

### Testing
```bash
# Run all tests
uv run pytest -v

# Run specific test types
uv run pytest -v -m unit          # Unit tests only
uv run pytest -v -m integration   # Integration tests only
uv run pytest -v -m e2e           # End-to-end tests (requires deployed infrastructure)

# Run with coverage
uv run pytest --cov=services --cov=libs --cov-report=html --cov-fail-under=80
```

### Code Quality
```bash
# Format code
uv run black services libs tests
uv run isort services libs tests

# Lint and type checking
uv run ruff check services libs tests
uv run mypy services libs

# Security scanning
uv run bandit -r services libs

# Run all quality checks (used in CI)
uv run black --check services libs tests && \
uv run isort --check services libs tests && \
uv run ruff check services libs tests && \
uv run mypy services libs && \
uv run pytest --cov=services --cov=libs --cov-fail-under=80
```

### Deployment
```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

## Code Architecture Patterns

### Lambda Handler Pattern
Each Lambda follows this pattern:
1. **src/handler.py**: Entry point with API Gateway event parsing and routing
2. **src/service.py**: Business logic separated from HTTP concerns
3. **src/models.py**: Pydantic models for request/response validation
4. **tests/**: Comprehensive unit and integration tests (outside src/)

### Error Handling
- Custom exceptions inherit from `PSNEmulatorException` ([libs/common/src/exceptions.py](libs/common/src/exceptions.py:4))
- Available exceptions:
  - `ValidationException` (400) - Request validation failures
  - `AuthenticationException` (401) - Authentication failures
  - `NotFoundException` (404) - Resource not found
  - `ConflictException` (409) - Resource conflicts
- Automatic error response formatting with proper HTTP status codes
- Structured logging with AWS Lambda Powertools

### Request/Response Validation
- All API inputs validated with Pydantic models
- Standardized response format via `APIResponse` and `ErrorResponse` models
- Type hints required on all functions
- JSON schema validation for all request bodies

### Logging
- Use `get_logger(__name__)` from [libs/common/src/logger.py](libs/common/src/logger.py:12)
- Never use `print()` statements
- Structured logging with contextual information
- Service name configured per Lambda (idp-api, player-account-api)

## Coding Standards

### Style Requirements
- **Black** formatting (line length 88)
- **isort** for import sorting
- **Ruff** for linting (strict rules with extensive selects)
- **mypy** for type checking (strict mode)
- All functions must have type hints
- Google-style docstrings required

### File Patterns
- **Source Code**: `{module}/src/` (e.g., `services/idp_api/src/`)
- **Tests**: `{module}/tests/` (outside src/)
- **Modules**: `lowercase_with_underscores.py`
- **Classes**: `PascalCase`
- **Functions**: `lowercase_with_underscores`
- **Constants**: `UPPERCASE_WITH_UNDERSCORES`

### Testing Requirements
- Minimum 80% test coverage across `services` and `libs`
- Unit tests for business logic (in `tests/unit/`)
- Integration tests for Lambda handlers (in `tests/integration/`)
- E2E tests for deployed infrastructure (in `tests/e2e/`)
- Use pytest fixtures for test setup

## API Endpoints

### IDP API (`/auth/*`)
- `POST /auth/token` - User authentication
  - Request: `AuthenticationRequest` (username, password, grant_type)
  - Response: `TokenResponse` (access_token, refresh_token, expires_in)
- `GET /auth/userinfo` - Get user information (requires Bearer token)
  - Headers: `Authorization: Bearer <token>`
  - Response: `UserInfo` (user_id, username, email, is_active)
- `POST /auth/refresh` - Refresh access token
  - Request: `RefreshTokenRequest` (refresh_token, grant_type)
  - Response: `TokenResponse` (new access_token)

### Player Account API (`/players/*`)
- `POST /players` - Create player
  - Request: `CreatePlayerRequest` (username, email, display_name)
  - Response: `PlayerAccount` (player_id, username, email, status, level, etc.)
- `GET /players` - List all players
  - Response: `{"players": [...], "count": N}`
- `GET /players/{player_id}` - Get specific player
  - Response: `PlayerAccount`
- `PUT /players/{player_id}` - Update player
  - Request: `UpdatePlayerRequest` (display_name, email, status)
  - Response: Updated `PlayerAccount`
- `DELETE /players/{player_id}` - Delete player
  - Response: 204 No Content
- `GET /players/{player_id}/stats` - Get player statistics
  - Response: `PlayerStats` (total_games, wins, losses, win_rate, playtime)

## Configuration Details

### pyproject.toml
- Project name: `fips-psn-emulator-service`
- Python requirement: >=3.13
- Main dependencies: pydantic, aws-lambda-powertools, boto3, requests
- Dev dependencies: pytest, black, ruff, mypy, bandit, pre-commit
- Build backend: hatchling with packages = ["libs/*/src/**", "services/*/src/**"]

### Pre-commit Hooks
- Black code formatting
- isort import sorting
- Ruff linting with auto-fix
- mypy type checking
- Bandit security scanning
- General file checks (whitespace, JSON/YAML validation)

### Terraform Configuration
- Provider: AWS v5.0+, Terraform v1.5.0+
- Backend: S3 (configurable)
- Variables: environment, region, lambda settings, logging options
- Resources:
  - API Gateway HTTP API with CORS
  - Lambda functions with proper IAM roles
  - CloudWatch log groups with configurable retention
  - Optional X-Ray tracing
- **Lambda Packaging**: Each Lambda packaged from its `src/` directory separately

### VS Code Debugging
Configurations available in `.vscode/launch.json`:
- **Debug: IDP API Lambda** - `services.idp_api.src.handler`
- **Debug: Player Account API Lambda** - `services.player_account_api.src.handler`
- **Python: All Unit Tests** - Runs all unit tests
- **Python: All Integration Tests** - Runs all integration tests

## Common Development Tasks

### Adding a New Lambda Function
1. Create directory: `services/new_api/src/`
2. Add files: `handler.py`, `service.py`, `models.py`, `__init__.py`
3. Follow existing patterns from other Lambdas
4. Update Terraform configuration in `infra/terraform/lambda.tf`
5. Add API Gateway routes in `infra/terraform/api_gateway.tf`
6. Update pyproject.toml if needed for new dependencies

### Adding Shared Libraries
1. Add code to `libs/common/src/`
2. Update imports in Lambda files: `from libs.common.src.module import ...`
3. Run tests to ensure imports work correctly

### Debugging
- Use VS Code debugging configurations (see `.vscode/launch.json`)
- Debug configurations available for individual Lambda handlers
- Test locally with mock events
- View CloudWatch logs after deployment

### Local Testing with Mock Events
Create test event JSON files and use handlers directly:
```python
from services.idp_api.src.handler import lambda_handler
import json

with open('test_event.json') as f:
    event = json.load(f)
response = lambda_handler(event, None)
```

## Environment Variables

### Development
Set in local `.env` file (not committed):
- `ENVIRONMENT=dev`
- `LOG_LEVEL=DEBUG`
- `AWS_REGION=us-east-1`

### Production
Configured in Terraform `infra/terraform/lambda.tf` for each Lambda function:
- `ENVIRONMENT` (dev/test/prod)
- `LOG_LEVEL` (INFO for prod, DEBUG for others)
- `POWERTOOLS_SERVICE_NAME` (per Lambda)

## Security Considerations

- All inputs validated with Pydantic models
- No secrets in code - use environment variables or AWS Secrets Manager
- Least privilege IAM roles defined in Terraform
- Security scanning with Bandit in CI/CD pipeline
- CORS configuration in API Gateway
- Token-based authentication for protected endpoints

## Deployment Notes

- **Separate Lambda Packaging**: Each Lambda packaged from its own `src/` directory
- Terraform manages Lambda package creation automatically
- Changes to Lambda code trigger updates via `source_code_hash`
- API Gateway routes configured in `infra/terraform/api_gateway.tf`
- Multi-environment support via Terraform variables
- Lambda packaging excludes tests and cache files
- Log retention configurable (default 7 days)

## Troubleshooting

### Common Issues
1. **Import errors in Lambda**: Check packaging paths in Terraform (`source_dir` should point to `src/`)
2. **Permission denied**: Update IAM roles in `infra/terraform/lambda.tf`
3. **Cold start latency**: Consider Lambda warming or memory increase
4. **Test failures locally**: Run `rm -rf .venv && uv sync`
5. **Type checking errors**: Check imports and type hints in strict mode
6. **Module not found errors**: Verify import paths match new `src/` structure

### Debug Mode
Enable detailed logging with `LOG_LEVEL=DEBUG` environment variable.

### Viewing Logs
```bash
# IDP API logs
aws logs tail /aws/lambda/psn-emulator-dev-idp-api --follow

# Player Account API logs
aws logs tail /aws/lambda/psn-emulator-dev-player-account-api --follow

# API Gateway logs (if enabled)
aws logs tail /aws/apigateway/psn-emulator-dev --follow
```

### Terraform Issues
- Backend configuration required for state management
- Ensure AWS credentials are properly configured
- Check variable values match expected types and constraints
- Use `terraform validate` and `terraform plan` before applying
- Verify `source_dir` paths in Lambda configurations point to correct `src/` directories

## Recent Structural Changes Summary

1. **src/ Directory Migration**: All Python source code moved to `src/` directories
2. **Import Path Updates**: All imports updated to reflect new structure
3. **Terraform Updates**: Lambda packaging now uses `src/` directories
4. **Build Configuration**: pyproject.toml updated for new package locations
5. **Debugging Configurations**: VS Code launch configs updated for new module paths

These changes provide better organization, cleaner deployments, and clearer separation between source code and tests.