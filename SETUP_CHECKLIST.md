# Setup Checklist for PSN Partner Emulator Service

Use this checklist to verify your setup and get started with development or deployment.

## ✅ Initial Setup

### Prerequisites Installation
- [ ] Python 3.12+ installed (`python --version`)
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
- [ ] Check formatting: `uv run black --check src tests`
- [ ] Check linting: `uv run ruff check src tests`
- [ ] Check types: `uv run mypy src`

## ✅ Development Environment

### VS Code Setup
- [ ] Open project in VS Code
- [ ] Install recommended extensions (prompted automatically)
- [ ] Verify Python interpreter is set to `.venv/bin/python`
- [ ] Test debugging: Open handler.py and press F5

### Git Configuration
- [ ] Initialize git: `git init` (if not already done)
- [ ] Create `.gitignore` (already present)
- [ ] Make initial commit: `git add . && git commit -m "feat: initial setup"`
- [ ] Connect to remote repository (if applicable)

## ✅ Code Quality Checks

Run all checks before committing:
- [ ] Format code: `uv run black src tests`
- [ ] Sort imports: `uv run isort src tests`
- [ ] Lint: `uv run ruff check src tests`
- [ ] Type check: `uv run mypy src`
- [ ] Security scan: `uv run bandit -r src`
- [ ] Run tests: `uv run pytest --cov=src --cov-fail-under=80`

## ✅ Local Testing

### Unit Tests
- [ ] Run all unit tests: `uv run pytest -v -m unit`
- [ ] Verify coverage: `uv run pytest --cov=src --cov-report=html`
- [ ] Open coverage report: `open htmlcov/index.html`

### Integration Tests
- [ ] Run integration tests: `uv run pytest -v -m integration`
- [ ] Test IDP API Lambda locally
- [ ] Test Player Account API Lambda locally

## ✅ AWS Deployment (Optional)

### AWS Prerequisites
- [ ] AWS account created
- [ ] AWS CLI installed: `aws --version`
- [ ] AWS credentials configured: `aws configure`
- [ ] Verify credentials: `aws sts get-caller-identity`

### Terraform Setup
- [ ] Terraform installed: `terraform --version`
- [ ] Navigate to terraform directory: `cd terraform`
- [ ] Initialize Terraform: `terraform init`
- [ ] Configure variables in `terraform.tfvars`

### Deploy Infrastructure
- [ ] Review plan: `terraform plan`
- [ ] Apply infrastructure: `terraform apply`
- [ ] Note API Gateway URL: `terraform output api_gateway_url`
- [ ] Test deployed API with curl commands

### Post-Deployment Verification
- [ ] Test authentication endpoint
- [ ] Test player creation endpoint
- [ ] View Lambda logs in CloudWatch
- [ ] Verify API Gateway metrics

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

- [ ] Read [README.md](README.md) - Main documentation
- [ ] Read [CONTRIBUTING.md](CONTRIBUTING.md) - Development guidelines
- [ ] Read [terraform/README.md](terraform/README.md) - Deployment guide
- [ ] Read [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Project overview
- [ ] Review [.github/copilot-instructions.md](.github/copilot-instructions.md) for AI assistance

## ✅ First Development Task

Ready to add a new feature? Follow this workflow:

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes**
   - Add/modify code in `src/`
   - Add tests in appropriate `tests/` directory
   - Update documentation if needed

3. **Run quality checks**
   ```bash
   uv run black src tests && \
   uv run isort src tests && \
   uv run ruff check src tests && \
   uv run mypy src && \
   uv run pytest --cov=src
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
uv sync                          # Install dependencies
uv run pytest -v                 # Run tests
uv run pytest --cov=src          # Run with coverage
uv run black src tests           # Format code
uv run ruff check src tests      # Lint code
uv run mypy src                  # Type check
```

### Deployment
```bash
cd terraform
terraform init                   # Initialize
terraform plan                   # Preview changes
terraform apply                  # Deploy
terraform output api_gateway_url # Get API URL
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

1. **Python version**: Must be 3.12+
2. **Dependencies**: Run `uv sync` again
3. **Virtual environment**: Ensure `.venv` is activated
4. **AWS credentials**: Run `aws sts get-caller-identity`
5. **Terraform state**: Check for state lock issues

For more help, see:
- README.md troubleshooting section
- CONTRIBUTING.md for development questions
- Open an issue on GitHub

## ✅ All Set!

Once all checkboxes are complete, you're ready to:
- Develop new Lambda functions
- Deploy to AWS
- Run full test suite
- Contribute to the project

**Happy coding!** 🚀
