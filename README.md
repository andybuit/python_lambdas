# PSN Partner Emulator Service

A serverless API service for simulating partner environments, enabling early integration, validation, and QA of PSN software without requiring access to partner production or QA systems.

## Overview

The PSN Partner Emulator provides:
- **IDP API**: Identity Provider emulation for authentication and token management
- **Player Account API**: Player account management and statistics tracking
- **Serverless Architecture**: AWS Lambda functions with API Gateway
- **Independent Services**: Each Lambda can be developed, tested, and deployed independently

## Architecture

```
┌─────────────────┐
│  API Gateway    │
│  (HTTP API)     │
└────────┬────────┘
         │
    ┌────┴────────────────┐
    │                     │
┌───▼────────┐    ┌──────▼──────┐
│ IDP API    │    │ Player      │
│ Lambda     │    │ Account API │
│            │    │ Lambda      │
└────────────┘    └─────────────┘
```

## Tech Stack

- **Language**: Python 3.12
- **Package Manager**: uv (fast Python package manager)
- **Framework**: AWS Lambda Powertools
- **Validation**: Pydantic v2
- **Testing**: pytest with coverage
- **Linting**: Ruff, Black, mypy, Bandit
- **Infrastructure**: Terraform
- **CI/CD**: GitHub Actions

## Prerequisites

### Required
- **Python 3.12+**: [Download Python](https://www.python.org/downloads/)
- **uv**: Fast Python package manager
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Git**: Version control

### For Deployment
- **AWS CLI**: [Install AWS CLI](https://aws.amazon.com/cli/)
- **Terraform**: [Install Terraform](https://www.terraform.io/downloads)
- **AWS Account**: With appropriate permissions

### Recommended
- **VS Code**: With recommended extensions (see `.vscode/extensions.json`)
- **Docker**: For local testing with containerized dependencies

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd fips-psn-emulator-service
```

### 2. Set Up Development Environment

```bash
# Install dependencies
uv sync

# Activate virtual environment (if needed)
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Install pre-commit hooks
uv run pre-commit install
```

### 3. Verify Installation

```bash
# Run tests
uv run pytest -v

# Check code quality
uv run black --check src tests
uv run ruff check src tests
uv run mypy src
```

## Development Workflow

### Project Structure

```
fips-psn-emulator-service/
├── src/
│   ├── lambdas/                 # Lambda functions
│   │   ├── idp_api/            # Identity Provider API
│   │   │   ├── handler.py      # Lambda handler
│   │   │   ├── service.py      # Business logic
│   │   │   ├── models.py       # Pydantic models
│   │   │   └── tests/          # Unit & integration tests
│   │   └── player_account_api/ # Player Account API
│   │       ├── handler.py
│   │       ├── service.py
│   │       ├── models.py
│   │       └── tests/
│   └── shared/                  # Shared utilities
│       ├── models.py           # Common models
│       ├── logger.py           # Logging utilities
│       └── exceptions.py       # Custom exceptions
├── tests/
│   └── e2e/                    # End-to-end tests
├── terraform/                   # Infrastructure as Code
│   ├── main.tf
│   ├── lambda.tf
│   ├── api_gateway.tf
│   └── variables.tf
├── .vscode/                    # VS Code configuration
├── .github/                    # GitHub Actions & Copilot instructions
├── pyproject.toml              # Project configuration
└── README.md                   # This file
```

### Running Locally

#### Run Tests

```bash
# All tests
uv run pytest -v

# Unit tests only
uv run pytest -v -m unit

# Integration tests
uv run pytest -v -m integration

# With coverage report
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html  # View coverage report
```

#### Code Formatting

```bash
# Format code
uv run black src tests
uv run isort src tests

# Check formatting (CI mode)
uv run black --check src tests
uv run isort --check src tests
```

#### Linting and Type Checking

```bash
# Lint code
uv run ruff check src tests

# Auto-fix issues
uv run ruff check --fix src tests

# Type checking
uv run mypy src

# Security scanning
uv run bandit -r src
```

#### Run All Quality Checks

```bash
# Single command for all checks
uv run black --check src tests && \
uv run isort --check src tests && \
uv run ruff check src tests && \
uv run mypy src && \
uv run pytest
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
from src.lambdas.idp_api.handler import lambda_handler
import json

with open('test_event.json') as f:
    event = json.load(f)

response = lambda_handler(event, None)
print(json.dumps(response, indent=2))
```

### Debugging in VS Code

1. Open VS Code
2. Set breakpoints in your code
3. Press `F5` or use Run & Debug panel
4. Select debug configuration:
   - "Debug: IDP API Lambda"
   - "Debug: Player Account API Lambda"
   - "Python: pytest" (for tests)

## Building for Deployment

### Build Lambda Packages

Lambda packages are automatically built by Terraform, but you can build manually:

```bash
# Create build directory
mkdir -p build

# Install dependencies to build directory
uv pip install --target build/python -r pyproject.toml

# Package Lambda
cd src
zip -r ../build/lambda.zip .
cd ..
```

### Package with Dependencies

For production deployments with dependencies:

```bash
# Install production dependencies
uv pip install --python-platform linux --python-version 3.12 \
  -r pyproject.toml --target build/python/lib/python3.12/site-packages

# Create layer
cd build
zip -r lambda-layer.zip python
cd ..
```

## Deployment

### Prerequisites for Deployment

1. **AWS Credentials**: Configure AWS CLI
   ```bash
   aws configure
   # Enter: AWS Access Key ID, Secret Access Key, Region, Output format
   ```

2. **S3 Bucket for Terraform State** (recommended):
   ```bash
   aws s3 mb s3://your-terraform-state-bucket
   ```

### Deploy with Terraform

#### 1. Initialize Terraform

```bash
cd terraform
terraform init
```

#### 2. Configure Variables

Create `terraform.tfvars`:

```hcl
aws_region              = "us-east-1"
environment             = "dev"
project_name            = "psn-emulator"
lambda_timeout          = 30
lambda_memory_size      = 512
log_retention_days      = 7
enable_api_gateway_logging = true
```

#### 3. Plan Deployment

```bash
terraform plan
```

Review the planned changes.

#### 4. Deploy Infrastructure

```bash
terraform apply
```

Type `yes` to confirm.

#### 5. Get API Gateway URL

```bash
terraform output api_gateway_url
```

### Testing Deployed API

```bash
# Set API URL
export API_URL=$(cd terraform && terraform output -raw api_gateway_url)

# Test IDP API - Authentication
curl -X POST $API_URL/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'

# Save token
export TOKEN="<access_token_from_response>"

# Test IDP API - Get user info
curl -X GET $API_URL/auth/userinfo \
  -H "Authorization: Bearer $TOKEN"

# Test Player Account API - Create player
curl -X POST $API_URL/players \
  -H "Content-Type: application/json" \
  -d '{"username":"player1","email":"player1@example.com"}'

# Test Player Account API - Get player
curl -X GET $API_URL/players/<player_id>

# Test Player Account API - List players
curl -X GET $API_URL/players
```

### Update Deployed Lambda

After code changes:

```bash
cd terraform
terraform apply
```

Terraform detects code changes via `source_code_hash` and updates Lambdas automatically.

### Destroy Infrastructure

```bash
cd terraform
terraform destroy
```

## Environment Variables

### Lambda Function Environment Variables

Set in Terraform (`lambda.tf`):

```hcl
environment {
  variables = {
    ENVIRONMENT             = var.environment
    LOG_LEVEL              = "DEBUG"
    POWERTOOLS_SERVICE_NAME = "idp-api"
  }
}
```

### Local Development Environment Variables

Create `.env` file (not committed):

```bash
ENVIRONMENT=dev
LOG_LEVEL=DEBUG
AWS_REGION=us-east-1
```

## API Documentation

### IDP API Endpoints

#### POST /auth/token
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

#### GET /auth/userinfo
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

#### POST /auth/refresh
Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "..."
}
```

### Player Account API Endpoints

#### POST /players
Create a new player account.

**Request:**
```json
{
  "username": "player1",
  "email": "player1@example.com",
  "display_name": "Player One"
}
```

#### GET /players
List all player accounts.

#### GET /players/{player_id}
Get specific player account.

#### PUT /players/{player_id}
Update player account.

**Request:**
```json
{
  "display_name": "Updated Name",
  "status": "active"
}
```

#### DELETE /players/{player_id}
Delete player account.

#### GET /players/{player_id}/stats
Get player statistics.

## Monitoring and Logging

### View Lambda Logs

```bash
# IDP API logs
aws logs tail /aws/lambda/psn-emulator-dev-idp-api --follow

# Player Account API logs
aws logs tail /aws/lambda/psn-emulator-dev-player-account-api --follow

# Filter for errors
aws logs tail /aws/lambda/psn-emulator-dev-idp-api --follow --filter-pattern "ERROR"
```

### CloudWatch Insights Queries

```sql
# Error analysis
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100

# Performance metrics
stats avg(@duration), max(@duration), min(@duration) by bin(5m)
```

### X-Ray Tracing

Enable X-Ray in `terraform.tfvars`:
```hcl
enable_xray_tracing = true
```

## Troubleshooting

### Common Issues

#### 1. Import Errors in Lambda

**Problem**: `ModuleNotFoundError` when Lambda executes

**Solution**: Ensure dependencies are included in Lambda package or use Lambda layers

#### 2. Permission Denied

**Problem**: Lambda can't access AWS services

**Solution**: Update IAM role in `terraform/lambda.tf` with required permissions

#### 3. Cold Start Latency

**Problem**: First request is slow

**Solutions**:
- Use Lambda warming (scheduled events)
- Optimize imports (lazy loading)
- Increase memory allocation
- Use Provisioned Concurrency

#### 4. Tests Failing Locally

**Problem**: Tests pass in CI but fail locally

**Solution**:
```bash
# Clean environment
rm -rf .venv
uv sync
uv run pytest -v
```

#### 5. Terraform State Lock

**Problem**: Terraform state is locked

**Solution**:
```bash
terraform force-unlock <lock-id>
```

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or set environment variable:
```bash
export LOG_LEVEL=DEBUG
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines, coding standards, and contribution workflow.

## Recommended Frameworks and Toolkits

### For Lambda Development
- **AWS Lambda Powertools**: Logging, tracing, metrics (✓ Already integrated)
- **AWS SAM CLI**: Local testing with `sam local start-api`
- **LocalStack**: Local AWS emulation for testing

### For Testing
- **moto**: AWS service mocking (✓ Already included)
- **pytest-asyncio**: Async test support
- **Tavern**: YAML-based API testing

### For API Documentation
- **FastAPI**: Consider migrating to FastAPI for auto-generated docs
- **OpenAPI**: Generate OpenAPI spec from code
- **Swagger UI**: Interactive API documentation

### For Observability
- **AWS X-Ray**: Distributed tracing (configurable)
- **CloudWatch Insights**: Log analysis
- **Datadog/New Relic**: Advanced monitoring (optional)

## Performance Optimization

### Lambda Cold Start Optimization
- Minimize dependencies
- Use Lambda layers for common dependencies
- Lazy load heavy imports
- Increase memory allocation (improves CPU)

### Cost Optimization
- Use ARM64 (Graviton2) for 20% cost reduction
- Adjust memory/timeout to minimum needed
- Implement caching for repeated queries
- Use DynamoDB On-Demand pricing for variable load

## Security Best Practices

1. **Secrets Management**: Use AWS Secrets Manager (implement as needed)
2. **Input Validation**: All inputs validated with Pydantic
3. **Least Privilege IAM**: Lambda roles have minimal permissions
4. **API Gateway**: Configure throttling and WAF (implement as needed)
5. **Security Scanning**: Bandit runs in CI/CD pipeline

## License

[Specify your license here]

## Support

For issues, questions, or contributions:
- Create an issue in the repository
- Review [CONTRIBUTING.md](CONTRIBUTING.md)
- Check existing issues and discussions

## Roadmap

### Phase 1 (Current)
- ✅ IDP API Lambda
- ✅ Player Account API Lambda
- ✅ Terraform infrastructure
- ✅ CI/CD pipeline

### Phase 2 (Planned)
- [ ] DynamoDB integration for persistence
- [ ] JWT token validation
- [ ] API Gateway authorizer
- [ ] Additional partner APIs

### Phase 3 (Future)
- [ ] GraphQL support
- [ ] WebSocket APIs
- [ ] Real-time event streaming
- [ ] Advanced analytics

## Acknowledgments

Built following PSN coding standards and AWS serverless best practices.
