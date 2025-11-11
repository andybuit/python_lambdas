# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **PSN Partner Emulator Service** (`fips-psn-emulator-service`) - a serverless AWS Lambda application that emulates partner API environments for early integration, validation, and QA of PSN software without requiring access to partner production systems.

### Architecture

The project follows a **Docker-based microservices pattern** with:
- **API Gateway HTTP API**: Single entry point that routes to different Lambda functions
- **Two Lambda Functions** (deployed as Docker containers):
  - `idp_api` - Identity Provider API for authentication and token management
  - `player_account_api` - Player account management and statistics
- **Shared Libraries**: Common utilities, models, exceptions, and logging in `libs/common/`
- **Terraform Infrastructure**: Infrastructure as Code for AWS deployment in `infra/terraform/`
- **Amazon ECR**: Container registry for Lambda Docker images

### Key Technologies

- **Python 3.13+** with **uv** package manager
- **Docker** for containerized Lambda deployment
- **AWS Lambda Powertools v3.4.0+** for structured logging and utilities
- **Pydantic v2.10.0+** for request/response validation
- **pytest v8.3.0+** for testing with comprehensive coverage
- **Terraform v1.5.0+** for infrastructure deployment
- **Amazon ECR** for Docker image storage

## Project Structure

```
python_lambdas/
├── .claude/                      # Claude Code configuration
├── .vscode/                      # VS Code debugging configurations
├── libs/                         # Shared libraries across Lambdas
│   └── common/                   # Common utilities
│       ├── pyproject.toml        # Common library dependencies
│       └── src/                  # Source code
│           ├── exceptions.py     # Custom exception hierarchy
│           ├── logger.py         # AWS Lambda Powertools logger
│           └── models.py         # Common response models
├── services/                     # Lambda functions (services)
│   ├── idp_api/                  # Identity Provider API Lambda
│   │   ├── Dockerfile            # Multi-stage Docker build
│   │   ├── pyproject.toml        # Function-specific dependencies
│   │   ├── src/                  # Source code
│   │   │   ├── handler.py        # Lambda entry point with routing
│   │   │   ├── service.py        # Business logic
│   │   │   └── models.py         # Pydantic request/response models
│   │   ├── tests/                # Unit and integration tests
│   │   │   ├── integration/
│   │   │   └── unit/
│   └── player_account_api/       # Player Account API Lambda
│       ├── Dockerfile            # Multi-stage Docker build
│       ├── pyproject.toml        # Function-specific dependencies
│       ├── src/                  # Source code
│       └── tests/                # Unit and integration tests
│           ├── integration/
│           └── unit/
├── scripts/                      # Root-level orchestration scripts
│   ├── build.py                  # Consolidated build script for all Lambdas
│   ├── test.py                   # Consolidated pytest runner for all Lambdas
│   └── deploy.py                 # Deploy images to AWS
├── infra/                        # Infrastructure as Code
│   └── terraform/                # Terraform configurations
│       ├── main.tf               # Provider and backend configuration
│       ├── ecr.tf                # ECR repositories for Docker images
│       ├── lambda.tf             # Lambda function definitions (container-based)
│       ├── api_gateway.tf        # API Gateway routing
│       ├── variables.tf          # Input variables
│       └── outputs.tf            # Output values (includes ECR URLs)
├── pyproject.toml                # Root project configuration (deprecated for Lambda code)
├── README.md                     # Project documentation
├── README_DOCKER.md              # Docker deployment guide
├── SETUP_CHECKLIST.md            # Setup checklist for developers
└── CLAUDE.md                     # This file - Claude Code guidance
```

## NEW: Docker-Based Architecture

### Per-Lambda Independence
Each Lambda function is **completely independent**:
- **Separate `pyproject.toml`**: Only includes dependencies needed by that specific function
- **Separate `Dockerfile`**: Multi-stage build optimized for that function
- **Independent builds**: Each Lambda can be built and deployed separately
- **Isolated dependencies**: No unnecessary packages included

### Benefits
- **Smaller Lambda images**: Only required dependencies included
- **Faster builds**: Changes to one Lambda don't require rebuilding others
- **Better security**: Minimal attack surface per function
- **Independent versioning**: Each Lambda can have different versions deployed

### Docker Multi-Stage Builds
All Dockerfiles use multi-stage builds:
1. **Builder stage**: Installs `uv`, syncs dependencies, builds packages
2. **Runtime stage**: Copies only runtime artifacts from builder (no build tools)

This results in minimal final image sizes.

## Development Commands

### Environment Setup
```bash
# Install uv package manager
pip install uv

# No need to sync at root - each Lambda is independent
```

### Building Docker Images

```bash
# Build a specific Lambda
uv run python scripts/build.py --service idp_api --tag v1.0.0

# Build all Lambdas
uv run python scripts/build.py --service all --tag v1.0.0

# Build without cache (clean build)
uv run python scripts/build.py --service all --no-cache --tag v1.0.0

# Build multiple specific services
uv run python scripts/build.py --service idp_api player_account_api --tag v1.0.0

# Build and push to ECR
uv run python scripts/build.py --service all --tag v1.0.0 --push --ecr-repo-map '{"idp_api": "123456789012.dkr.ecr.us-east-1.amazonaws.com/fips-psn-idp-api", "player_account_api": "123456789012.dkr.ecr.us-east-1.amazonaws.com/fips-psn-player-account-api"}'
```

### Testing

```bash
# Test a specific Lambda
uv run python scripts/test.py --service idp_api --coverage --html

# Test all Lambdas
uv run python scripts/test.py --service all --coverage

# Run only unit tests
uv run python scripts/test.py --service all --type unit --verbose

# Run only integration tests
uv run python scripts/test.py --service all --type integration --verbose

# Run tests in parallel
uv run python scripts/test.py --service all --parallel --workers 4

# Run with coverage and HTML report
uv run python scripts/test.py --service all --coverage --html --html-dir coverage_report
```

### Deployment

```bash
# Deploy infrastructure first (creates ECR repos)
cd infra/terraform
terraform init
terraform plan
terraform apply

# Build and deploy all Lambdas
uv run python scripts/deploy.py --tag v1.0.0 --environment dev

# Deploy specific Lambda only
uv run python scripts/deploy.py --tag v1.0.0 --services idp_api --environment dev

# Deploy without building (use existing local images)
uv run python scripts/deploy.py --tag v1.0.0 --no-build --environment dev
```

## Code Architecture Patterns

### Lambda Handler Pattern
Each Lambda follows this pattern:
1. **src/handler.py**: Entry point with API Gateway event parsing and routing
2. **src/service.py**: Business logic separated from HTTP concerns
3. **src/models.py**: Pydantic models for request/response validation
4. **tests/**: Comprehensive unit and integration tests (outside src/)
5. **Dockerfile**: Multi-stage build for containerized deployment
6. **pyproject.toml**: Function-specific dependencies only
7. **pytest**: Testing with unit and integration markers

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
- **Scripts**: `{module}/scripts/` (build.py, test.py)
- **Modules**: `lowercase_with_underscores.py`
- **Classes**: `PascalCase`
- **Functions**: `lowercase_with_underscores`
- **Constants**: `UPPERCASE_WITH_UNDERSCORES`

### Testing Requirements
- Each Lambda maintains its own test coverage (target: 80%+)
- Unit tests for business logic (in `tests/unit/`)
- Integration tests for Lambda handlers (in `tests/integration/`)
- E2E tests for deployed infrastructure (in root `tests/e2e/`)
- Use pytest fixtures for test setup
- Use consolidated test script: `uv run python scripts/test.py --service <service_name>`
- Mark tests with `@pytest.mark.unit` or `@pytest.mark.integration`
- Run tests with coverage: `uv run python scripts/test.py --service all --coverage --html`

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
- `GET /players` - List all players
- `GET /players/{player_id}` - Get specific player
- `PUT /players/{player_id}` - Update player
- `DELETE /players/{player_id}` - Delete player
- `GET /players/{player_id}/stats` - Get player statistics

## Configuration Details

### Per-Lambda pyproject.toml
Each Lambda has minimal dependencies:

**IDP API** (`services/idp_api/pyproject.toml`):
```toml
dependencies = [
    "pydantic[email]>=2.10.0",
    "aws-lambda-powertools>=3.4.0",
]
```

**Player Account API** (`services/player_account_api/pyproject.toml`):
```toml
dependencies = [
    "pydantic[email]>=2.10.0",
    "aws-lambda-powertools>=3.4.0",
]
```

**Common Library** (`libs/common/pyproject.toml`):
```toml
dependencies = [
    "pydantic>=2.10.0",
    "aws-lambda-powertools>=3.4.0",
]
```

### Terraform Configuration
- Provider: AWS v5.0+, Terraform v1.5.0+
- Backend: S3 (configurable)
- Variables: environment, region, lambda settings, image tags, logging options
- Resources:
  - **ECR repositories** (one per Lambda) with lifecycle policies
  - API Gateway HTTP API with CORS
  - Lambda functions with **container image package type**
  - CloudWatch log groups with configurable retention
  - Optional X-Ray tracing
- **Lambda Packaging**: Each Lambda deployed as Docker container from ECR

### Docker Configuration
- Base image: `public.ecr.aws/lambda/python:3.13`
- Multi-stage builds for minimal image size
- Common library installed from local path during build
- Environment variables set in Lambda configuration (Terraform)

### VS Code Debugging
Configurations available in `.vscode/launch.json`:
- **Debug: IDP API Lambda** - `services.idp_api.src.handler`
- **Debug: Player Account API Lambda** - `services.player_account_api.src.handler`
- **Python: All Unit Tests** - Runs all unit tests
- **Python: All Integration Tests** - Runs all integration tests

## Common Development Tasks

### Adding a New Lambda Function
1. Create directory structure:
   ```
   services/new_api/
   ├── Dockerfile
   ├── pyproject.toml
   ├── src/
   │   ├── __init__.py
   │   ├── handler.py
   │   ├── service.py
   │   └── models.py
   ├── tests/
   │   ├── unit/
   │   └── integration/
   └── scripts/
       ├── build.py
       └── test.py
   ```
2. Copy and modify Dockerfile from existing Lambda
3. Create `pyproject.toml` with only needed dependencies
4. Add ECR repository in `infra/terraform/ecr.tf`
5. Add Lambda function in `infra/terraform/lambda.tf`
6. Add API Gateway routes in `infra/terraform/api_gateway.tf`
7. Update `scripts/build_all.py` and `scripts/deploy.py` to include new service

### Adding Dependencies to a Lambda
1. Edit the Lambda's `pyproject.toml`:
   ```toml
   dependencies = [
       "pydantic[email]>=2.10.0",
       "aws-lambda-powertools>=3.4.0",
       "new-package>=1.0.0",  # Add here
   ]
   ```
2. Rebuild the Docker image:
   ```bash
   cd services/{lambda_name}
   uv run python scripts/build.py --tag v1.1.0 --no-cache
   ```
3. Test and deploy:
   ```bash
   uv run python scripts/test.py --coverage
   python ../../scripts/deploy.py --tag v1.1.0 --services {lambda_name}
   ```

### Adding Shared Libraries
1. Add code to `libs/common/src/`
2. Update `libs/common/pyproject.toml` if new dependencies needed
3. Rebuild ALL Lambda images (since they include common library):
   ```bash
   python scripts/build_all.py --tag v1.1.0 --no-cache
   ```
4. Run tests to ensure imports work correctly
5. Deploy all Lambdas

### Debugging Locally
1. **With Docker:**
   ```bash
   # Build the image
   python services/idp_api/scripts/build.py --tag dev

   # Run locally
   docker run -p 9000:8080 fips-psn-idp-api:dev

   # Test with curl
   curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
     -d '{"body": "{\"username\":\"testuser\",\"password\":\"password123\"}"}'
   ```

2. **With VS Code:**
   - Use the debugging configurations in `.vscode/launch.json`
   - Debug configurations available for individual Lambda handlers

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
- ECR image scanning enabled (scans on push)
- CORS configuration in API Gateway
- Token-based authentication for protected endpoints
- Docker multi-stage builds reduce attack surface

## Deployment Notes

- **Container-Based Deployment**: Lambdas deployed as Docker images from ECR
- Each Lambda has its own ECR repository
- Terraform uses `image_uri` with `package_type = "Image"`
- `lifecycle.ignore_changes` on `image_uri` allows updates without Terraform
- Image tags configurable via Terraform variables
- Deploy script handles building, pushing, and Lambda updates
- Multi-environment support via Terraform workspaces/variables

## Troubleshooting

### Common Issues
1. **Docker build fails**: Check Docker is running, try `--no-cache`
2. **uv sync errors**: Update uv (`pip install --upgrade uv`), clear cache
3. **ECR authentication fails**: Run `aws ecr get-login-password` manually
4. **Lambda update fails**: Verify ECR image exists, check Lambda IAM permissions
5. **Import errors in Lambda**: Check Dockerfile COPY paths, verify common library location
6. **Test failures locally**: Run `uv sync` in Lambda directory

### Debug Mode
Enable detailed logging with `LOG_LEVEL=DEBUG` environment variable.

### Viewing Logs
```bash
# IDP API logs
aws logs tail /aws/lambda/psn-emulator-dev-idp-api --follow

# Player Account API logs
aws logs tail /aws/lambda/psn-emulator-dev-player-account-api --follow
```

### Terraform Issues
- Run `terraform init` after adding new resources
- Use `terraform validate` before apply
- Check `image_uri` points to valid ECR repository
- Ensure ECR repositories exist before creating Lambda functions
- Verify Docker images are pushed before deploying

## Cross-Platform Support

All Python scripts work on **Windows, Linux, and macOS**:
- Use `python` or `python3` depending on system
- Scripts use `Path` from `pathlib` for cross-platform paths
- No bash scripts - all orchestration in Python
- Docker commands work identically across platforms

**Windows (PowerShell):**
```powershell
uv run python scripts\build.py --service all --tag v1.0.0
uv run python scripts\test.py --service all --coverage
```

**Linux/macOS:**
```bash
python3 scripts/build.py --service all --tag v1.0.0
python3 scripts/test.py --service all --coverage
```

## Additional Documentation

- [README_DOCKER.md](README_DOCKER.md) - Detailed Docker deployment guide
- [README.md](README.md) - Project overview and setup
- [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md) - Setup checklist

## Recent Architectural Changes

### Migration to Docker-Based Deployment
- **From**: ZIP-based Lambda deployment with shared dependencies
- **To**: Docker container images with per-Lambda dependencies
- **Benefits**:
  - Isolated dependencies per Lambda
  - Smaller deployment artifacts
  - Better reproducibility
  - Industry-standard containerization

### Per-Lambda Configuration
- Each Lambda now has its own `pyproject.toml` with minimal dependencies
- No more monolithic dependency file
- Common library packaged separately and included during Docker build

### Cross-Platform Build System
- Python-based build scripts (not bash)
- Work identically on Windows, Linux, and macOS
- Consistent developer experience across platforms
