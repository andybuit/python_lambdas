# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **PSN Partner Emulator Service** - a serverless AWS Lambda application that emulates partner API environments for early integration, validation, and QA of PSN software without requiring access to partner production systems.

### Architecture

The project follows a **serverless microservices pattern** with:
- **API Gateway HTTP API**: Single entry point that routes to different Lambda functions
- **Two Lambda Functions**:
  - `idp_api` - Identity Provider API for authentication and token management
  - `player_account_api` - Player account management and statistics
- **Shared Layer**: Common utilities, models, exceptions, and logging
- **Terraform Infrastructure**: Infrastructure as Code for AWS deployment

### Key Technologies

- **Python 3.12** with **uv** package manager
- **AWS Lambda Powertools** for structured logging and utilities
- **Pydantic v2** for request/response validation
- **pytest** for testing with comprehensive coverage
- **Terraform** for infrastructure deployment

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
uv run pytest --cov=src --cov-report=html --cov-fail-under=80
```

### Code Quality
```bash
# Format code
uv run black src tests
uv run isort src tests

# Lint and type checking
uv run ruff check src tests
uv run mypy src

# Security scanning
uv run bandit -r src

# Run all quality checks (used in CI)
uv run black --check src tests && \
uv run isort --check src tests && \
uv run ruff check src tests && \
uv run mypy src && \
uv run pytest --cov=src --cov-fail-under=80
```

### Deployment
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## Project Structure

```
src/
├── services/                # Lambda functions (services)
│   ├── idp_api/              # Identity Provider API Lambda
│   │   ├── handler.py        # Lambda entry point with routing
│   │   ├── service.py        # Business logic
│   │   ├── models.py         # Pydantic request/response models
│   │   └── tests/            # Unit and integration tests
│   └── player_account_api/   # Player Account API Lambda
│       ├── handler.py
│       ├── service.py
│       ├── models.py
│       └── tests/
└── libs/                    # Shared libraries across Lambdas
    ├── models.py             # Common response models (APIResponse, ErrorResponse)
    ├── logger.py             # AWS Lambda Powertools logger configuration
    └── exceptions.py         # Custom exception hierarchy

tests/
└── e2e/                      # End-to-end tests for deployed infrastructure

terraform/                    # Infrastructure as Code
├── main.tf                   # Provider and backend configuration
├── lambda.tf                 # Lambda function definitions
├── api_gateway.tf            # API Gateway routing
├── variables.tf              # Input variables
└── outputs.tf                # Output values
```

## Code Architecture Patterns

### Lambda Handler Pattern
Each Lambda follows this pattern:
1. **handler.py**: Entry point with API Gateway event parsing and routing
2. **service.py**: Business logic separated from HTTP concerns
3. **models.py**: Pydantic models for request/response validation
4. **tests/**: Comprehensive unit and integration tests

### Error Handling
- Custom exceptions inherit from `PSNEmulatorException` ([src/libs/exceptions.py](src/libs/exceptions.py:4))
- Automatic error response formatting with proper HTTP status codes
- Structured logging with AWS Lambda Powertools

### Request/Response Validation
- All API inputs validated with Pydantic models
- Standardized response format via `APIResponse` and `ErrorResponse` models
- Type hints required on all functions

### Logging
- Use `get_logger(__name__)` from [src/libs/logger.py](src/libs/logger.py)
- Never use `print()` statements
- Structured logging with contextual information

## Coding Standards

### Style Requirements
- **Black** formatting (line length 88)
- **isort** for import sorting
- **Ruff** for linting (strict rules)
- **mypy** for type checking (strict mode)
- All functions must have type hints
- Google-style docstrings required

### File Patterns
- Modules: `lowercase_with_underscores.py`
- Classes: `PascalCase`
- Functions: `lowercase_with_underscores`
- Constants: `UPPERCASE_WITH_UNDERSCORES`

### Testing Requirements
- Minimum 80% test coverage
- Unit tests for business logic
- Integration tests for Lambda handlers
- Use pytest fixtures for test setup

## API Endpoints

### IDP API (`/auth/*`)
- `POST /auth/token` - User authentication
- `GET /auth/userinfo` - Get user information (requires Bearer token)
- `POST /auth/refresh` - Refresh access token

### Player Account API (`/players/*`)
- `POST /players` - Create player
- `GET /players` - List all players
- `GET /players/{player_id}` - Get specific player
- `PUT /players/{player_id}` - Update player
- `DELETE /players/{player_id}` - Delete player
- `GET /players/{player_id}/stats` - Get player statistics

## Common Development Tasks

### Adding a New Lambda Function
1. Create directory: `src/services/new_api/`
2. Add files: `handler.py`, `service.py`, `models.py`, `tests/`
3. Follow existing patterns from other Lambdas
4. Update Terraform configuration in `terraform/lambda.tf`
5. Add API Gateway routes in `terraform/api_gateway.tf`

### Debugging
- Use VS Code debugging configurations (see `.vscode/launch.json`)
- Test locally with mock events
- View CloudWatch logs after deployment

### Local Testing with Mock Events
Create test event JSON files and use handlers directly:
```python
from src.services.idp_api.handler import lambda_handler
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
Configured in Terraform `lambda.tf` for each Lambda function.

## Security Considerations

- All inputs validated with Pydantic models
- No secrets in code - use environment variables or AWS Secrets Manager
- Least privilege IAM roles defined in Terraform
- Security scanning with Bandit in CI/CD pipeline

## Deployment Notes

- Terraform manages Lambda package creation automatically
- Changes to Lambda code trigger updates via `source_code_hash`
- API Gateway routes configured in `terraform/api_gateway.tf`
- Multi-environment support via Terraform workspaces

## Troubleshooting

### Common Issues
1. **Import errors in Lambda**: Check packaging in Terraform
2. **Permission denied**: Update IAM roles in `terraform/lambda.tf`
3. **Cold start latency**: Consider Lambda warming or memory increase
4. **Test failures locally**: Run `rm -rf .venv && uv sync`

### Debug Mode
Enable detailed logging with `LOG_LEVEL=DEBUG` environment variable.

### Viewing Logs
```bash
# IDP API logs
aws logs tail /aws/lambda/psn-emulator-dev-idp-api --follow

# Player Account API logs
aws logs tail /aws/lambda/psn-emulator-dev-player-account-api --follow
```