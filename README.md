# PSN Partner Emulator Service

A serverless API service for simulating partner environments, enabling early integration, validation, and QA of PSN software without requiring access to partner production or QA systems.

## Overview

The PSN Partner Emulator provides a collection of independent serverless microservices with **two deployment options**:

- **IDP API**: Identity Provider emulation for authentication and token management
- **Player Account API**: Player account management and statistics tracking
- **Docker-Based Architecture**: Lambda functions deployed as container images with isolated dependencies
- **ZIP + Layers Architecture**: Lambda functions deployed as optimized ZIP packages with shared dependency layers
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
│(Container) │    │(Container)  │
└────────────┘    └─────────────┘
         │                     │
         └───────┬─────────────┘
                 │
        ┌────────▼────────┐
        │  Amazon ECR     │
        │  Container Reg  │
        └─────────────────┘
```

## Services

### IDP API

- **Purpose**: Authentication and token management
- **README**: [services/idp_api/README.md](services/idp_api/README.md)
- **Endpoints**: `/auth/*`

### Player Account API

- **Purpose**: Player account management and statistics
- **README**: [services/player_account_api/README.md](services/player_account_api/README.md)
- **Endpoints**: `/players/*`

## Tech Stack

- **Language**: Python 3.13
- **Package Manager**: uv (fast Python package manager)
- **Deployment**: Docker container images with AWS Lambda
- **Framework**: AWS Lambda Powertools v3.4.0+
- **Validation**: Pydantic v2.10.0+
- **Testing**: pytest v8.3.0+ with coverage
- **Linting**: Ruff, Black, mypy, Bandit
- **Infrastructure**: Terraform v1.5.0+
- **Container Registry**: Amazon ECR
- **CI/CD**: GitHub Actions (if configured)

## Prerequisites

### Required

- **Python 3.13+**: [Download Python](https://www.python.org/downloads/)
- **uv**: Fast Python package manager
  ```bash
  pip install uv
  ```
- **Docker**: [Install Docker](https://www.docker.com/get-started) (required for building Lambda images)
- **Git**: Version control

### For Deployment

- **AWS CLI**: [Install AWS CLI](https://aws.amazon.com/cli/)
- **Terraform v1.5+**: [Install Terraform](https://www.terraform.io/downloads)
- **AWS Account**: With appropriate permissions
- **Amazon ECR**: For storing Docker container images

### Recommended

- **VS Code**: With recommended extensions (see `.vscode/extensions.json`)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd fips-psn-emulator-service
```

### 2. Set Up Development Environment

```bash
# Install dependencies and create virtual environment
uv sync

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install pre-commit hooks (optional)
uv run pre-commit install  # Only if pre-commit is configured
```

### 3. Verify Installation

```bash
# Test individual Lambda functions using consolidated script
uv run python scripts/test.py --service idp_api --coverage --html
uv run python scripts/test.py --service player_account_api --coverage --html

# Test all Lambdas
uv run python scripts/test.py --service all --coverage --html
```

## Deployment Options

### Option 1: Docker-Based Deployment (Recommended)

Container-based deployment with isolated dependencies per Lambda.

**Getting Started with Docker:**
- See [README_DOCKER.md](README_DOCKER.md) for complete guide
- Use `scripts/build.py` to build Docker images
- Deploy via Terraform with ECR repositories

### Option 2: ZIP + Layers Deployment

Traditional ZIP deployment with shared dependency layers for optimal size and performance.

**Getting Started with ZIP:**
- See [scripts/README_ZIP_BUILD.md](scripts/README_ZIP_BUILD.md) for complete guide
- Use `scripts/build_zip.py` to create optimized packages that read from each service's `pyproject.toml`
- Upload layers and update Lambda functions

**Quick ZIP Build:**
```bash
# Build ZIP packages for all services (reads from each service's pyproject.toml)
uv run python scripts/build_zip.py

# Build for specific services only
uv run python scripts/build_zip.py --services idp_api player_account_api

# Clean build
uv run python scripts/build_zip.py --clean
```

**Comparison:**
| Feature | Docker | ZIP + Layers |
|---------|--------|--------------|
| Package Size | Larger | Smaller |
| Cold Starts | Slower | Faster |
| Dependencies | Full control | Layer constraints |
| Local Testing | Native | SAM/LocalStack |

## Development Workflow

### Project Structure

```
fips-psn-emulator-service/
├── services/                   # Lambda functions (independent containers)
│   ├── idp_api/                # Identity Provider API
│   │   ├── README.md           # Service-specific documentation
│   │   ├── Dockerfile          # Multi-stage Docker build
│   │   ├── pyproject.toml      # IDP API dependencies only
│   │   ├── src/                # Source code directory
│   │   │   ├── __init__.py
│   │   │   ├── handler.py      # Lambda handler
│   │   │   ├── service.py      # Business logic
│   │   │   └── models.py       # Pydantic models
│   │   ├── tests/              # Unit & integration tests
│   │   │   ├── unit/
│   │   │   └── integration/
│   └── player_account_api/     # Player Account API
│       ├── README.md           # Service-specific documentation
│       ├── Dockerfile          # Multi-stage Docker build
│       ├── pyproject.toml      # Player Account API dependencies only
│       ├── src/                # Source code directory
│       │   ├── __init__.py
│       │   ├── handler.py
│       │   ├── service.py
│       │   └── models.py
│       ├── tests/              # Unit & integration tests
│       │   ├── unit/
│       │   └── integration/
├── libs/                       # Shared libraries
│   └── common/                  # Common utilities
│       ├── pyproject.toml      # Common library dependencies
│       └── src/                # Source code directory
│           ├── __init__.py
│           ├── exceptions.py   # Custom exceptions
│           ├── logger.py       # AWS Lambda Powertools logger
│           └── models.py       # Common response models
├── scripts/                    # Orchestration scripts
│   ├── build.py                # Consolidated build script for all Lambdas
│   ├── test.py                 # Consolidated pytest runner for all Lambdas
│   └── deploy.py               # Deploy images to AWS
├── tests/
│   └── e2e/                    # End-to-end tests
├── infra/terraform/            # Infrastructure as Code
│   ├── main.tf                 # Provider and backend
│   ├── lambda.tf               # Lambda functions (container-based)
│   ├── api_gateway.tf          # API Gateway configuration
│   ├── ecr.tf                  # ECR repositories
│   ├── variables.tf            # Input variables
│   └── outputs.tf              # Output values
├── .vscode/                    # VS Code configuration
├── .claude/                    # Claude Code configuration
├── pyproject.toml              # Root project configuration (orchestration only)
├── pytest.ini                  # Legacy pytest configuration (per-Lambda configs preferred)
├── README.md                   # This file
├── README_DOCKER.md            # Docker deployment guide
├── SETUP_CHECKLIST.md          # Setup and verification checklist
├── MIGRATION_SUMMARY.md        # Docker migration details
├── CONTRIBUTING.md             # Development guidelines
├── PROJECT_SUMMARY.md          # Project overview
└── CLAUDE.md                   # Claude Code guidance
```

### Docker-Based Architecture

**Per-Lambda Independence:**

- Each Lambda has its own `Dockerfile` with multi-stage build
- Each Lambda has its own `pyproject.toml` with minimal dependencies
- Docker images built from `public.ecr.aws/lambda/python:3.13` base image
- Images pushed to Amazon ECR for Lambda deployment

**Key Benefits:**

- **Dependency Isolation**: Each Lambda only includes packages it needs
- **Smaller Images**: Multi-stage builds remove build tools from final image
- **Independent Deployment**: Update one Lambda without affecting others
- **Consistent Environment**: Same container runtime locally and in AWS

**Import Examples:**

```python
# Within Lambda files (relative imports)
from .models import AuthenticationRequest
from .service import IDPService

# Cross-module imports (common library)
from libs.common.src.exceptions import ValidationException
from libs.common.src.logger import get_logger
```

### Running Locally

#### Run Tests

```bash
# Test specific Lambda (recommended approach)
uv run python scripts/test.py --service idp_api --coverage --html

# Test another Lambda
uv run python scripts/test.py --service player_account_api --coverage --html

# Test all Lambdas
uv run python scripts/test.py --service all --coverage --html

# Run specific test types
uv run python scripts/test.py --service all --type unit --verbose
uv run python scripts/test.py --service all --type integration --verbose

# Run tests in parallel
uv run python scripts/test.py --service all --parallel --workers 4

# Build and test
uv run python scripts/build.py --service all --tag test
uv run python scripts/test.py --service all --coverage
```

#### Code Formatting and Quality

```bash
# For individual Lambda
cd services/idp_api
uv run black src/
uv run ruff check src/
uv run mypy src/

# Or use the consolidated test script which includes quality checks
uv run python scripts/test.py --service idp_api --coverage --html
```

### Local Testing with Docker

#### Test Lambda Containers Locally

```bash
# Build IDP API image
uv run python scripts/build.py --service idp_api --tag local

# Run Lambda locally
docker run -p 9000:8080 fips-psn-idp-api:local

# In another terminal, test with mock event
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{
    "httpMethod": "POST",
    "path": "/auth/token",
    "body": "{\"username\":\"testuser\",\"password\":\"password123\"}"
  }'
```

#### Test Handler Code Directly

```python
# Test handler directly (requires Python environment setup)
from services.idp_api.src.handler import lambda_handler
import json

event = {
    "httpMethod": "POST",
    "path": "/auth/token",
    "body": "{\"username\":\"testuser\",\"password\":\"password123\"}"
}

response = lambda_handler(event, None)
print(json.dumps(response, indent=2))
```

### Debugging in VS Code

1. Open VS Code
2. Set breakpoints in your code
3. Press `F5` or use Run & Debug panel
4. Select debug configuration:
   - "Debug: IDP API Lambda" (`services.idp_api.src.handler`)
   - "Debug: Player Account API Lambda" (`services.player_account_api.src.handler`)
   - "Python: pytest" (for tests)

## Building Docker Images

### Build Individual Lambda

```bash
# Build specific Lambda with tag
uv run python scripts/build.py --service idp_api --tag v1.0.0

# Build without cache (clean build)
uv run python scripts/build.py --service idp_api --no-cache --tag v1.0.0
```

### Build All Lambdas

```bash
# Build all Lambda images
uv run python scripts/build.py --service all --tag v1.0.0

# Build specific services only
uv run python scripts/build.py --service idp_api player_account_api --tag v1.0.0

# Build without cache
uv run python scripts/build.py --service all --no-cache --tag v1.0.0

# Build and push to ECR
uv run python scripts/build.py --service all --tag v1.0.0 --push --ecr-repo-map '{"idp_api": "123456789012.dkr.ecr.us-east-1.amazonaws.com/fips-psn-idp-api", "player_account_api": "123456789012.dkr.ecr.us-east-1.amazonaws.com/fips-psn-player-account-api"}'
```

### Test Docker Images

```bash
# Verify images were built
docker images | findstr fips-psn

# Test image locally
docker run -p 9000:8080 fips-psn-idp-api:v1.0.0
```

## Deployment

### Prerequisites for Deployment

1. **AWS Credentials**: Configure AWS CLI

   ```bash
   aws configure
   # Enter: AWS Access Key ID, Secret Access Key, Region, Output format
   ```

2. **Verify Docker and AWS Access**:
   ```bash
   docker --version
   aws sts get-caller-identity
   ```

### Deploy Infrastructure and Images

#### Step 1: Deploy AWS Infrastructure

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

This creates:

- ECR repositories for each Lambda
- Lambda functions (placeholder images initially)
- API Gateway configuration
- IAM roles and permissions

#### Step 2: Build and Deploy Lambda Images

```bash
# Build and deploy all Lambdas
python scripts/deploy.py --tag v1.0.0 --environment dev

# Deploy specific Lambda only
python scripts/deploy.py --tag v1.0.0 --services idp_api --environment dev

# Deploy without building (use existing local images)
python scripts/deploy.py --tag v1.0.0 --no-build --environment dev
```

#### Step 3: Get API Gateway URL

```bash
cd infra/terraform
terraform output api_gateway_url
```

### Testing Deployed API

For comprehensive testing examples, see the individual service README files:

- **IDP API Testing**: [services/idp_api/README.md#testing](services/idp_api/README.md#testing)
- **Player Account API Testing**: [services/player_account_api/README.md#testing](services/player_account_api/README.md#testing)

Quick examples:

```bash
# Set API URL
export API_URL=$(cd infra/terraform && terraform output -raw api_gateway_url)

# Test IDP API - Authentication
curl -X POST $API_URL/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'

# Test Player Account API - Create player
curl -X POST $API_URL/players \
  -H "Content-Type: application/json" \
  -d '{"username":"player1","email":"player1@example.com"}'
```

### Update Deployed Lambda

After code changes:

```bash
# Option 1: Build and deploy specific Lambda
uv run python scripts/build.py --service idp_api --tag v1.0.1
uv run python scripts/deploy.py --tag v1.0.1 --services idp_api --environment dev

# Option 2: Build and deploy all
uv run python scripts/build.py --service all --tag v1.0.1
uv run python scripts/deploy.py --tag v1.0.1 --environment dev
```

### Destroy Infrastructure

```bash
cd infra/terraform
terraform destroy
```

**Note**: This will also delete ECR repositories and all Docker images.

## Environment Variables

### Lambda Function Environment Variables

Set in Terraform (`infra/terraform/lambda.tf`):

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

### Available Endpoints

**IDP API (`/auth/*`)**

- `POST /auth/token` - User authentication
- `GET /auth/userinfo` - Get user information (requires Bearer token)
- `POST /auth/refresh` - Refresh access token

**Player Account API (`/players/*`)**

- `POST /players` - Create player
- `GET /players` - List all players
- `GET /players/{player_id}` - Get specific player
- `PUT /players/{player_id}` - Update player
- `DELETE /players/{player_id}` - Delete player
- `GET /players/{player_id}/stats` - Get player statistics

### Detailed Documentation

For comprehensive API documentation and examples, see the individual service README files:

- **IDP API**: [services/idp_api/README.md](services/idp_api/README.md)

  - Authentication endpoints with request/response examples
  - Token management and validation
  - User information retrieval

- **Player Account API**: [services/player_account_api/README.md](services/player_account_api/README.md)
  - Player account management operations
  - Player statistics tracking
  - Profile management endpoints

### Quick API Examples

```bash
# Get API Gateway URL from Terraform
export API_URL=$(cd infra/terraform && terraform output -raw api_gateway_url)

# Test IDP API - Authentication
curl -X POST $API_URL/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'

# Test Player Account API - Create player
curl -X POST $API_URL/players \
  -H "Content-Type: application/json" \
  -d '{"username":"player1","email":"player1@example.com"}'
```

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

#### 1. Docker Build Fails

**Problem**: Docker build fails with errors

**Solution**:

```bash
# Check Docker is running
docker ps

# Clean Docker cache
docker system prune -a

# Rebuild without cache
uv run python scripts/build.py --service all --no-cache --tag v1.0.0

# Update uv if needed
pip install --upgrade uv
```

#### 2. Import Errors in Lambda

**Problem**: `ModuleNotFoundError` when Lambda executes

**Solution**:

- Check Dockerfile copies all necessary files from `src/` directories
- Verify common library is copied to correct path in container
- Check Lambda handler path in Terraform configuration
- Rebuild with `--no-cache` to ensure fresh dependencies

#### 3. ECR Authentication Issues

**Problem**: Cannot push images to ECR

**Solution**:

```bash
# Verify AWS credentials
aws sts get-caller-identity

# Get ECR login manually
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
```

#### 4. Lambda Update Fails

**Problem**: Lambda function update fails

**Solution**:

```bash
# Check Lambda exists
aws lambda list-functions --query 'Functions[?contains(FunctionName, `psn-emulator`)].FunctionName'

# Check ECR image exists
aws ecr describe-images --repository-name psn-emulator-dev-idp-api

# Verify image URI in Terraform output
cd infra/terraform
terraform output ecr_repository_idp_api
```

#### 5. Cold Start Latency

**Problem**: First request is slow

**Solutions**:

- Optimize Docker image size (multi-stage builds already configured)
- Lazy load heavy imports in Lambda code
- Increase memory allocation (improves CPU)
- Use Provisioned Concurrency for critical functions

#### 6. Tests Failing Locally

**Problem**: Tests fail when running locally

**Solution**:

```bash
# Ensure dependencies are installed for specific Lambda
cd services/idp_api
uv sync

# Run tests with verbose output (from project root)
cd ../..
uv run python scripts/test.py --service idp_api --type unit --verbose

# Check imports work with new structure
python -c "from services.idp_api.src.handler import lambda_handler; print('Import OK')"
```

#### 7. Terraform State Lock

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

For new developers, follow the [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md) to verify your environment setup and understand the project structure.

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

### Phase 1 (Current) ✅

- ✅ IDP API Lambda with authentication and token management
- ✅ Player Account API Lambda with player management
- ✅ Individual service documentation
- ✅ Test organization (unit/integration)
- ✅ Terraform infrastructure
- ✅ **NEW**: Docker-based Lambda deployment with container images
- ✅ **NEW**: Per-Lambda dependency isolation
- ✅ **NEW**: Multi-stage Docker builds for optimization
- ✅ **NEW**: Cross-platform Python build and test scripts
- ✅ **NEW**: ECR repository management for container images

### Phase 2 (Planned)

- [ ] DynamoDB integration for persistence
- [ ] JWT token validation with proper signing
- [ ] API Gateway authorizer for protected endpoints
- [ ] Additional partner APIs
- [ ] Service-specific monitoring and alerting
- [ ] Automated API documentation generation
- [ ] GitHub Actions CI/CD pipeline (if needed)

### Phase 3 (Future)

- [ ] GraphQL support
- [ ] WebSocket APIs
- [ ] Real-time event streaming
- [ ] Advanced analytics
- [ ] Service mesh integration
- [ ] Multi-region deployment

## Acknowledgments

Built following PSN coding standards and AWS serverless best practices.
