# Docker-Based Lambda Deployment Guide

This project uses **Docker container images** for AWS Lambda deployment, providing isolated dependencies and consistent builds across environments.

## Architecture Overview

### Per-Lambda Configuration
Each Lambda function has its own:
- `pyproject.toml` - Function-specific dependencies only
- `Dockerfile` - Multi-stage build with Python 3.13
- `tests/` - Unit and integration tests
- Uses consolidated build and test scripts from root `scripts/` directory

### Shared Common Library
The `libs/common/` directory contains shared code:
- Exception classes
- Logger configuration
- Common Pydantic models

## Project Structure

```
├── libs/common/              # Shared library
│   ├── pyproject.toml        # Common dependencies
│   └── src/                  # Source code
├── services/
│   ├── idp_api/              # IDP API Lambda
│   │   ├── Dockerfile        # Container build
│   │   ├── pyproject.toml    # Function dependencies
│   │   ├── src/              # Source code
│   │   └── tests/            # Unit & integration tests
│   └── player_account_api/   # Player Account API Lambda
│       ├── Dockerfile
│       ├── pyproject.toml
│       ├── src/
│       └── tests/
├── scripts/
│   ├── build.py              # Consolidated build script
│   ├── test.py               # Consolidated test script
│   ├── build_all.py          # Legacy build script (deprecated)
│   └── deploy.py             # Deploy to AWS
└── infra/terraform/          # Infrastructure as Code
    ├── ecr.tf                # ECR repositories
    └── lambda.tf             # Lambda functions (container-based)
```

## Prerequisites

### Required Tools
- **Python 3.13+**
- **uv package manager** - Install: `pip install uv`
- **Docker** - Install from [docker.com](https://www.docker.com/get-started)
- **AWS CLI** - Install from [aws.amazon.com/cli](https://aws.amazon.com/cli/)
- **Terraform 1.5+** - Install from [terraform.io](https://www.terraform.io/downloads)

### AWS Configuration
```bash
# Configure AWS credentials
aws configure

# Verify access
aws sts get-caller-identity
```

## Building Lambda Images

### Build Individual Lambda

**All Platforms:**
```bash
uv run python scripts/build.py --service idp_api --tag v1.0.0
```

### Build All Lambdas

**All Platforms:**
```bash
uv run python scripts/build.py --service all --tag v1.0.0
```

### Build Options
```bash
# Build with custom tag
uv run python scripts/build.py --service all --tag v1.0.0

# Build without cache (clean build)
uv run python scripts/build.py --service all --no-cache

# Build specific services only
uv run python scripts/build.py --service idp_api player_account_api

# Build for different platform
uv run python scripts/build.py --service all --platform linux/arm64

# Build and push to ECR
uv run python scripts/build.py --service all --push --ecr-repo-map '{"idp_api": "123456789012.dkr.ecr.us-east-1.amazonaws.com/fips-psn-idp-api", "player_account_api": "123456789012.dkr.ecr.us-east-1.amazonaws.com/fips-psn-player-account-api"}'
```

## Testing Lambda Functions

### Test Individual Lambda

**Run all tests:**
```bash
uv run python scripts/test.py --service idp_api --verbose --coverage
```

**Run unit tests only:**
```bash
uv run python scripts/test.py --service idp_api --type unit --verbose
```

**Run integration tests only:**
```bash
uv run python scripts/test.py --service idp_api --type integration --verbose
```

**Generate HTML coverage report:**
```bash
uv run python scripts/test.py --service idp_api --coverage --html
```

### Test Both Lambdas
```bash
# Test all services with coverage
uv run python scripts/test.py --service all --coverage --html

# Test with parallel execution
uv run python scripts/test.py --service all --parallel --workers 4
```

## Deploying to AWS

### Step 1: Initialize Infrastructure

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

This creates:
- ECR repositories for each Lambda
- Lambda functions (placeholder images)
- API Gateway configuration
- IAM roles and permissions

### Step 2: Build and Push Images

**Build and push all services:**
```bash
python scripts/deploy.py --tag v1.0.0 --environment dev
```

**Deploy specific service:**
```bash
python scripts/deploy.py --tag v1.0.0 --services idp_api --environment dev
```

**Deploy without building (use existing local images):**
```bash
python scripts/deploy.py --tag v1.0.0 --no-build --environment dev
```

### Step 3: Verify Deployment

```bash
# Get API Gateway URL
cd infra/terraform
terraform output api_gateway_url

# Test the endpoints
curl -X POST <API_URL>/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'
```

## Development Workflow

### 1. Make Code Changes
Edit files in `services/{lambda_name}/src/`

### 2. Run Tests Locally
```bash
cd services/{lambda_name}
python scripts/test.py --coverage --html
```

### 3. Build Docker Image
```bash
python scripts/build.py --tag dev
```

### 4. Test Docker Image Locally (Optional)
```bash
docker run -p 9000:8080 fips-psn-{lambda-name}:dev

# In another terminal
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{"body": "{\"username\":\"testuser\",\"password\":\"password123\"}"}'
```

### 5. Deploy to AWS
```bash
python scripts/deploy.py --tag dev --services {lambda_name}
```

## Dependency Management

### Adding Dependencies to a Lambda

1. **Edit the Lambda's `pyproject.toml`:**
```toml
# services/idp_api/pyproject.toml
dependencies = [
    "pydantic[email]>=2.10.0",
    "aws-lambda-powertools>=3.4.0",
    "new-package>=1.0.0",  # Add new dependency
]
```

2. **Rebuild the Docker image:**
```bash
cd services/idp_api
python scripts/build.py --tag v1.1.0 --no-cache
```

3. **Test and deploy:**
```bash
python scripts/test.py --coverage
python ../../scripts/deploy.py --tag v1.1.0 --services idp_api
```

### Adding Dependencies to Common Library

1. **Edit `libs/common/pyproject.toml`:**
```toml
dependencies = [
    "pydantic>=2.10.0",
    "aws-lambda-powertools>=3.4.0",
    "new-shared-package>=1.0.0",  # Add here
]
```

2. **Rebuild ALL Lambda images** (since they use the common library):
```bash
python scripts/build_all.py --tag v1.1.0 --no-cache
```

## Troubleshooting

### Build Issues

**Docker build fails:**
```bash
# Check Docker is running
docker ps

# Clean Docker cache
docker system prune -a

# Rebuild without cache
python scripts/build.py --no-cache
```

**uv sync fails:**
```bash
# Update uv
pip install --upgrade uv

# Clear uv cache
uv cache clean

# Rebuild
python scripts/build.py --no-cache
```

### Deployment Issues

**ECR authentication fails:**
```bash
# Get ECR login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Verify credentials
aws sts get-caller-identity
```

**Lambda update fails:**
```bash
# Check Lambda exists
aws lambda list-functions --query 'Functions[?contains(FunctionName, `psn-emulator`)].FunctionName'

# Check ECR image exists
aws ecr describe-images --repository-name psn-emulator-dev-idp-api
```

**Import errors in Lambda:**
- Check Dockerfile copies all necessary files
- Verify common library is copied to correct path
- Check Lambda handler path in Terraform

### Testing Issues

**Tests fail locally:**
```bash
# Ensure dependencies are installed
cd services/{lambda_name}
uv sync

# Run with verbose output
python scripts/test.py --type unit --verbose
```

**Coverage too low:**
```bash
# Generate HTML report to see gaps
python scripts/test.py --coverage --html

# Open htmlcov/index.html in browser
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python 3.13
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install uv
        run: pip install uv

      - name: Run tests
        run: |
          cd services/idp_api && python scripts/test.py --coverage
          cd ../player_account_api && python scripts/test.py --coverage

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Build and deploy
        run: python scripts/deploy.py --tag ${{ github.sha }} --environment prod
```

## Best Practices

### Version Tagging
- Use semantic versioning: `v1.0.0`, `v1.1.0`, etc.
- Tag with git commit SHA for CI/CD: `git rev-parse --short HEAD`
- Keep `latest` tag for development

### Dependency Isolation
- Only add dependencies to a Lambda if that Lambda needs them
- Keep common library minimal - only truly shared code
- Review `pyproject.toml` regularly to remove unused dependencies

### Testing
- Maintain >80% code coverage
- Run tests before every build
- Use integration tests to verify handler logic
- Test locally with Docker before deploying

### Security
- Scan images: `docker scan fips-psn-idp-api:latest`
- Enable ECR image scanning (already configured)
- Rotate AWS credentials regularly
- Never commit credentials to git

### Performance
- Use multi-stage Docker builds (already configured)
- Keep Lambda images small (only runtime dependencies)
- Monitor cold start times in CloudWatch
- Consider Lambda reserved concurrency for critical functions

## Additional Resources

- [AWS Lambda Container Images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
- [uv Package Manager](https://github.com/astral-sh/uv)
- [Docker Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
