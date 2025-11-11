# Setup Checklist for PSN Partner Emulator Service

Use this checklist to verify your setup and get started with development or deployment.

## ✅ Initial Setup

### Prerequisites Installation
- [ ] Python 3.13+ installed (`python --version`) **🆕 Updated requirement**
- [ ] uv package manager installed (`uv --version`)
- [ ] Git installed (`git --version`)
- [ ] VS Code installed (recommended)

### Project Setup
- [ ] Clone/navigate to project directory
- [ ] Run `uv sync` to install dependencies
- [ ] Activate virtual environment (optional, uv handles this)
- [ ] Install pre-commit hooks: `uv run pre-commit install`

### Verify Installation
- [ ] Run tests: `uv run pytest -v`
- [ ] Check formatting: `uv run black --check services libs tests`
- [ ] Check linting: `uv run ruff check services libs tests`
- [ ] Check types: `uv run mypy services libs`

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
- [ ] Format code: `uv run black services libs tests`
- [ ] Sort imports: `uv run isort services libs tests`
- [ ] Lint: `uv run ruff check services libs tests`
- [ ] Type check: `uv run mypy services libs`
- [ ] Security scan: `uv run bandit -r services libs`
- [ ] Run tests: `uv run pytest --cov=services --cov=libs --cov-fail-under=80` **🆕 Added libs coverage**

## ✅ Understanding the Project Structure

### 🆕 NEW: src/ Directory Organization
- [ ] Review the new `src/` directory structure:
  - Lambda code: `services/{name}/src/`
  - Shared libraries: `libs/common/src/`
  - Tests: Remain outside `src/` directories
- [ ] Understand import patterns:
  - Within Lambda: `from .models import ...`
  - Cross-module: `from libs.common.src.exceptions import ...`

### Key Files to Understand
- [ ] Review `services/idp_api/src/handler.py` - Lambda entry point **🆕 Updated path**
- [ ] Review `services/idp_api/src/service.py` - Business logic **🆕 Updated path**
- [ ] Review `libs/common/src/exceptions.py` - Shared exceptions **🆕 Updated path**
- [ ] Review `infra/terraform/lambda.tf` - Infrastructure configuration

## ✅ Local Testing

### Unit Tests
- [ ] Run all unit tests: `uv run pytest -v -m unit`
- [ ] Verify coverage: `uv run pytest --cov=services --cov=libs --cov-report=html`
- [ ] Open coverage report: `open htmlcov/index.html`

### Integration Tests
- [ ] Run integration tests: `uv run pytest -v -m integration`
- [ ] Test IDP API Lambda locally using new import paths:
  ```python
  from services.idp_api.src.handler import lambda_handler
  ```
- [ ] Test Player Account API Lambda locally using new import paths:
  ```python
  from services.player_account_api.src.handler import lambda_handler
  ```

### 🆕 Local Testing with Mock Events
- [ ] Create test event file `test_event.json`
- [ ] Test Lambda handlers with new structure:
  ```python
  from services.idp_api.src.handler import lambda_handler
  import json

  with open('test_event.json') as f:
      event = json.load(f)
  response = lambda_handler(event, None)
  ```

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

### 🆕 Deploy Infrastructure with src/ Structure
- [ ] Review plan: `terraform plan`
  - Verify `source_dir` paths point to `src/` directories
- [ ] Apply infrastructure: `terraform apply`
- [ ] Note API Gateway URL: `terraform output api_gateway_url`
- [ ] Test deployed API with curl commands

### Post-Deployment Verification
- [ ] Test authentication endpoint
- [ ] Test player creation endpoint
- [ ] View Lambda logs in CloudWatch
- [ ] Verify API Gateway metrics
- [ ] Check for import errors in Lambda logs (related to src/ structure)

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
- [ ] Install AWS SAM CLI for local testing
- [ ] Install LocalStack for local AWS emulation
- [ ] Set up Docker for containerized testing

## ✅ Documentation Review

- [ ] Read [README.md](README.md) - Main documentation **🆕 Updated with src/ structure**
- [ ] Read [CONTRIBUTING.md](CONTRIBUTING.md) - Development guidelines
- [ ] Read [CLAUDE.md](CLAUDE.md) - AI assistant guidance **🆕 Updated with src/ structure**
- [ ] Read [infra/terraform/README.md](infra/terraform/README.md) - Deployment guide
- [ ] Read [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Project overview

## ✅ First Development Task

Ready to add a new feature? Follow this workflow:

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes**
   - Add/modify code in `services/{name}/src/` or `libs/common/src/` **🆕 Updated paths**
   - Add tests in appropriate `tests/` directory
   - Update documentation if needed

3. **Run quality checks**
   ```bash
   uv run black services libs tests && \
   uv run isort services libs tests && \
   uv run ruff check services libs tests && \
   uv run mypy services libs && \
   uv run pytest --cov=services --cov=libs
   ```

4. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add your feature"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## 🎯 Quick Reference Commands

### Development
```bash
uv sync                              # Install dependencies
uv run pytest -v                     # Run tests
uv run pytest --cov=services --cov=libs  # Run with coverage **🆕 Added libs**
uv run black services libs tests     # Format code
uv run ruff check services libs tests # Lint code
uv run mypy services libs            # Type check
```

### 🆕 Testing with New Structure
```bash
# Test specific Lambda with new imports
uv run python -c "from services.idp_api.src.handler import lambda_handler; print('Import OK')"

# Run tests for specific service
uv run pytest services/idp_api/tests/unit/
uv run pytest services/player_account_api/tests/unit/
```

### Deployment
```bash
cd infra/terraform
terraform init                       # Initialize
terraform plan                       # Preview changes
terraform apply                      # Deploy
terraform output api_gateway_url     # Get API URL
```

### Testing Deployed API
```bash
export API_URL=<your-api-url>
curl -X POST $API_URL/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'
```

## 🆘 Troubleshooting

If you encounter issues, check:

1. **Python version**: Must be 3.13+ **🆕 Updated requirement**
2. **Dependencies**: Run `uv sync` again
3. **Virtual environment**: Ensure `.venv` is activated
4. **Import errors**: Check import paths use new `src/` structure:
   - Libraries: `from libs.common.src.exceptions import ...`
   - Services: `from services.idp_api.src.handler import ...`
5. **AWS credentials**: Run `aws sts get-caller-identity`
6. **Terraform state**: Check for state lock issues
7. **Lambda deployment errors**: Verify Terraform `source_dir` paths point to `src/` directories

### Common Issues with New Structure

**ModuleNotFoundError**:
- Ensure imports use `src/` paths
- Check Terraform configuration points to correct directories
- Verify test imports use new structure

**Debugging Issues**:
- VS Code launch configurations use `services.idp_api.src.handler`
- Test local imports work with new structure

For more help, see:
- README.md troubleshooting section **🆕 Updated with src/ guidance**
- CONTRIBUTING.md for development questions
- CLAUDE.md for AI assistant guidance **🆕 Updated with src/ structure**
- Open an issue on GitHub

## ✅ All Set!

Once all checkboxes are complete, you're ready to:
- Develop new Lambda functions using `src/` structure **🆕 Updated**
- Deploy to AWS
- Run full test suite
- Contribute to the project

**Happy coding!** 🚀

---

## 📋 Recent Updates Summary

This checklist has been updated to reflect the following changes:

- ✅ **Python 3.13+ requirement** (updated from 3.12+)
- ✅ **New src/ directory structure** for all Python source code
- ✅ **Updated import patterns** for cross-module dependencies
- ✅ **Enhanced testing instructions** with new structure
- ✅ **Updated troubleshooting** for src/ related issues
- ✅ **Modified file paths** throughout documentation
- ✅ **Added libs coverage** to testing requirements