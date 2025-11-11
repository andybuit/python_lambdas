# Setup Checklist for PSN Partner Emulator Service

Use this checklist to verify your setup and get started with development or deployment.

## ✅ Initial Setup

### Prerequisites Installation
- [ ] Python 3.13+ installed (`python --version`)
- [ ] uv package manager installed (`pip install uv && uv --version`)
- [ ] Docker installed and running (`docker --version`)
- [ ] Git installed (`git --version`)
- [ ] VS Code installed (recommended)

### Project Setup
- [ ] Clone/navigate to project directory
- [ ] No root-level dependencies needed - each Lambda is independent
- [ ] Install pre-commit hooks: `uv run pre-commit install` (if configured)

### Verify Installation
- [ ] Test individual Lambda: `uv run python scripts/test.py --service idp_api --coverage --html`
- [ ] Test second Lambda: `uv run python scripts/test.py --service player_account_api --coverage --html`
- [ ] Test all Lambdas: `uv run python scripts/test.py --service all --coverage --html`
- [ ] Verify Docker builds: `uv run python scripts/build.py --service all --tag test`

## ✅ Development Environment

### VS Code Setup
- [ ] Open project in VS Code
- [ ] Install recommended extensions (prompted automatically)
- [ ] Verify Python interpreter is set to `.venv/bin/python`
- [ ] Test debugging: Open `services/idp_api/src/handler.py` and press F5 **🆕 Updated path**

### Git Configuration
- [ ] Initialize git: `git init` (if not already done)
- [ ] Create `.gitignore` (already present)
- [ ] Make initial commit: `git add . && git commit -m "feat: initial setup"`
- [ ] Connect to remote repository (if applicable)

## ✅ Code Quality Checks

Run all checks before committing:
- [ ] For IDP API: `uv run python scripts/test.py --service idp_api --coverage --html`
- [ ] For Player Account API: `uv run python scripts/test.py --service player_account_api --coverage --html`
- [ ] For all services: `uv run python scripts/test.py --service all --coverage --html`
- [ ] Format code (per service): `cd services/{name} && uv run black src/`
- [ ] Lint code (per service): `cd services/{name} && uv run ruff check src/`
- [ ] Type check (per service): `cd services/{name} && uv run mypy src/`
- [ ] Build Docker images: `uv run python scripts/build.py --service all --tag test`

## ✅ Understanding the Project Structure

### Docker-Based Architecture
- [ ] Review the Docker-based project structure:
  - Lambda code: `services/{name}/src/` (handler.py, service.py, models.py)
  - Shared libraries: `libs/common/src/` (exceptions.py, logger.py, models.py)
  - Tests: `services/{name}/tests/` with unit/ and integration/ subdirectories
  - Docker files: `services/{name}/Dockerfile` (multi-stage builds)
  - Centralized scripts: `scripts/build.py`, `scripts/test.py`, `scripts/deploy.py`
  - Pytest configuration: `pytest.ini`
  - Infrastructure: `infra/terraform/` with ECR and Lambda configurations
- [ ] Understand key benefits:
  - **Isolated dependencies** - Each Lambda has only required packages
  - **Smaller images** - Multi-stage builds remove build tools
  - **Independent deployment** - Each Lambda can be updated separately
  - **Consistent environment** - Docker eliminates "it works on my machine" issues
- [ ] Understand import patterns:
  - Within Lambda: `from .models import ...`
  - Cross-module: `from libs.common.src.exceptions import ...`
- [ ] Understand Docker deployment:
  - Images built with `public.ecr.aws/lambda/python:3.13` base
  - Multi-stage builds remove build tools from final image
  - Images pushed to Amazon ECR for Lambda deployment

### Key Files to Understand
- [ ] Review `services/idp_api/src/handler.py` - Lambda entry point
- [ ] Review `services/idp_api/src/service.py` - Business logic
- [ ] Review `services/idp_api/Dockerfile` - Multi-stage container build
- [ ] Review `scripts/build.py` - Consolidated build script
- [ ] Review `scripts/test.py` - Consolidated test script
- [ ] Review `pytest.ini` - Pytest configuration
- [ ] Review `libs/common/src/exceptions.py` - Shared exceptions
- [ ] Review `infra/terraform/lambda.tf` - Container-based Lambda configuration
- [ ] Review `infra/terraform/ecr.tf` - ECR repositories
- [ ] Review API endpoints documentation in README_DOCKER.md

## ✅ Local Testing

### Unit Tests
- [ ] Run IDP API unit tests: `uv run python scripts/test.py --service idp_api --type unit --verbose`
- [ ] Run Player Account API unit tests: `uv run python scripts/test.py --service player_account_api --type unit --verbose`
- [ ] Run all unit tests: `uv run python scripts/test.py --service all --type unit --verbose`
- [ ] Verify coverage: `uv run python scripts/test.py --service all --coverage --html`
- [ ] Open coverage reports: `open htmlcov/index.html` (generated per service)

### Integration Tests
- [ ] Run IDP API integration tests: `uv run python scripts/test.py --service idp_api --type integration --verbose`
- [ ] Run Player Account API integration tests: `uv run python scripts/test.py --service player_account_api --type integration --verbose`
- [ ] Run all integration tests: `uv run python scripts/test.py --service all --type integration --verbose`
- [ ] Run tests in parallel: `uv run python scripts/test.py --service all --parallel --workers 4`

### Local Docker Testing
- [ ] Build IDP API: `uv run python scripts/build.py --service idp_api --tag local`
- [ ] Test container locally: `docker run -p 9000:8080 fips-psn-idp-api:local`
- [ ] Test with mock event:
  ```bash
  curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
    -d '{"httpMethod":"POST","path":"/auth/token","body":"{\"username\":\"testuser\",\"password\":\"password123\"}"}'
  ```

### Local Code Testing
- [ ] Test IDP API handler directly: `python -c "from services.idp_api.src.handler import lambda_handler; print('Import OK')"`
- [ ] Test Player Account API handler directly: `python -c "from services.player_account_api.src.handler import lambda_handler; print('Import OK')"`

## ✅ AWS Deployment (Optional)

### AWS Prerequisites
- [ ] AWS account created
- [ ] AWS CLI installed: `aws --version`
- [ ] AWS credentials configured: `aws configure`
- [ ] Verify credentials: `aws sts get-caller-identity`

### Terraform Setup
- [ ] Terraform installed: `terraform --version`
- [ ] Navigate to terraform directory: `cd infra/terraform`
- [ ] Initialize Terraform: `terraform init`
- [ ] Configure variables in `terraform.tfvars`

### Deploy Docker-Based Infrastructure
- [ ] Review plan: `terraform plan`
- [ ] Apply infrastructure: `terraform apply` (creates ECR repos and Lambda placeholders)
- [ ] Note API Gateway URL: `terraform output api_gateway_url`
- [ ] Note ECR repository URLs: `terraform output ecr_repository_idp_api`
- [ ] Build and deploy Lambda images: `uv run python scripts/deploy.py --tag v1.0.0 --environment dev`

### Post-Deployment Verification
- [ ] Test authentication endpoint
- [ ] Test player creation endpoint
- [ ] View Lambda logs in CloudWatch
- [ ] Verify API Gateway metrics
- [ ] Check for import errors in Lambda logs (should be none with Docker images)
- [ ] Verify ECR images are deployed: `aws ecr describe-images --repository-name psn-emulator-dev-idp-api`

## ✅ Optional Enhancements

### CI/CD Setup
- [ ] Push to GitHub
- [ ] Verify GitHub Actions workflow runs
- [ ] Set up branch protection rules
- [ ] Configure required status checks

### Monitoring
- [ ] Enable X-Ray tracing (set `enable_xray_tracing = true`)
- [ ] Create CloudWatch dashboard
- [ ] Set up CloudWatch alarms
- [ ] Configure log insights queries

### Local Development Tools
- [ ] Docker for containerized testing (already required)
- [ ] Install AWS SAM CLI for local testing (optional)
- [ ] Install LocalStack for local AWS emulation (optional)

## ✅ Documentation Review

- [ ] Read [README.md](README.md) - Main documentation (updated for Docker)
- [ ] Read [README_DOCKER.md](README_DOCKER.md) - Docker deployment guide
- [ ] Read [MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md) - Docker migration details
- [ ] Read [CONTRIBUTING.md](CONTRIBUTING.md) - Development guidelines
- [ ] Read [CLAUDE.md](CLAUDE.md) - AI assistant guidance (updated for Docker)
- [ ] Read [infra/terraform/README.md](infra/terraform/README.md) - Deployment guide
- [ ] Read [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Project overview

## ✅ First Development Task

Ready to add a new feature? Follow this workflow:

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes**
   - Add/modify code in `services/{name}/src/` or `libs/common/src/`
   - Add tests in appropriate `tests/` directory
   - Update Dockerfile if dependencies changed
   - Update documentation if needed

3. **Run quality checks**
   ```bash
   # For the specific service you modified
   uv run python scripts/test.py --service {modified_service} --coverage --html
   uv run python scripts/build.py --service {modified_service} --tag dev

   # Or test all services
   uv run python scripts/test.py --service all --coverage --html
   uv run python scripts/build.py --service all --tag dev
   ```

4. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add your feature"
   ```

5. **Test and deploy**
   ```bash
   # Build all images
   uv run python scripts/build.py --service all --tag v1.0.1

   # Deploy to AWS
   uv run python scripts/deploy.py --tag v1.0.1 --environment dev
   ```

6. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## 🎯 Quick Reference Commands

### Development
```bash
# Test individual services
uv run python scripts/test.py --service idp_api --coverage --html
uv run python scripts/test.py --service player_account_api --coverage --html

# Test all services
uv run python scripts/test.py --service all --coverage --html

# Build Docker images
uv run python scripts/build.py --service all --tag v1.0.0

# Build specific services
uv run python scripts/build.py --service idp_api player_account_api --tag v1.0.0

# Format and lint (per service)
cd services/{name} && uv run black src/
cd services/{name} && uv run ruff check src/
cd services/{name} && uv run mypy src/
```

### Docker Testing
```bash
# Test imports work
python -c "from services.idp_api.src.handler import lambda_handler; print('Import OK')"
python -c "from services.player_account_api.src.handler import lambda_handler; print('Import OK')"

# Test containers locally
uv run python scripts/build.py --service idp_api --tag local
docker run -p 9000:8080 fips-psn-idp-api:local
```

### Deployment
```bash
# Deploy infrastructure
cd infra/terraform
terraform init                       # Initialize
terraform plan                       # Preview changes
terraform apply                      # Deploy ECR and Lambda placeholders

# Build and deploy images
uv run python scripts/deploy.py --tag v1.0.0 --environment dev

# Get API URL
terraform output api_gateway_url     # Get API URL
```

### Testing Deployed API
```bash
export API_URL=$(cd infra/terraform && terraform output -raw api_gateway_url)
curl -X POST $API_URL/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'
```

## 🆘 Troubleshooting

If you encounter issues, check:

1. **Docker**: Ensure Docker is running (`docker ps`)
2. **Python version**: Must be 3.13+
3. **uv package manager**: Ensure installed (`pip install uv`)
4. **Import errors**: Check import paths use correct structure:
   - Libraries in Lambda: `from libs.common.src.exceptions import ...`
   - Within Lambda: `from .models import RequestModel`
   - Service imports: `from .service import BusinessLogic`
5. **AWS credentials**: Run `aws sts get-caller-identity`
6. **ECR authentication**: Check Docker login to ECR registry
7. **Terraform state**: Check for state lock issues
8. **Lambda deployment errors**: Verify ECR images exist and are accessible

### Common Docker Issues

**Docker Build Fails**:
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
uv run python scripts/build.py --service all --no-cache --tag v1.0.0
```

**ECR Authentication Issues**:
```bash
# Get ECR login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
```

**Import Errors in Deployed Lambda**:
- Check Dockerfile copies all necessary files
- Verify common library path in container
- Rebuild with `--no-cache`

For more help, see:
- README.md troubleshooting section (updated for Docker)
- README_DOCKER.md for Docker-specific guidance
- CONTRIBUTING.md for development questions
- CLAUDE.md for AI assistant guidance (updated for Docker)
- Open an issue on GitHub

## ✅ All Set!

Once all checkboxes are complete, you're ready to:
- Develop new Lambda functions using Docker-based architecture
- Build and test Lambda container images
- Deploy to AWS using ECR and Terraform
- Run full test suite per service
- Contribute to the project

**Happy coding!** 🚀

---

## 📋 Recent Updates Summary

This checklist has been updated to reflect the following changes:

- ✅ **Docker-based Lambda deployment** with container images
- ✅ **Per-Lambda dependency isolation** using individual pyproject.toml files
- ✅ **Multi-stage Docker builds** for optimized images
- ✅ **Cross-platform Python build scripts** (Windows/Linux/macOS)
- ✅ **ECR integration** for container image storage
- ✅ **Consolidated build and test scripts** in root `scripts/` directory
- ✅ **pytest-based testing** with unit/integration markers
- ✅ **Parallel test execution** support with pytest-xdist
- ✅ **Docker as a prerequisite** for local development
- ✅ **Removed dependency on root-level pyproject.toml**
- ✅ **Individual service independence** for development and deployment
- ✅ **Centralized pytest configuration** in `pytest.ini`