# Contributing to PSN Partner Emulator

Thank you for your interest in contributing to the PSN Partner Emulator service! This document provides guidelines and best practices for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Commit Message Guidelines](#commit-message-guidelines)

## Code of Conduct

Be respectful, professional, and constructive in all interactions. We're here to build great software together.

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/fips-psn-emulator-service.git
cd fips-psn-emulator-service

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/fips-psn-emulator-service.git
```

### 2. Set Up Development Environment

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and create virtual environment
uv sync

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install pre-commit hooks
uv run pre-commit install

# Verify individual service pyproject.toml files are correctly configured
```

### 3. Create a Branch

```bash
# Update your fork
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

## Development Workflow

### 1. Make Your Changes

Follow the coding standards (see below) and ensure:
- Code is well-documented
- Type hints are used
- Tests are included
- Changes are focused and atomic

### 2. Run Quality Checks Locally

Before committing, run all quality checks:

```bash
# Format code
uv run black services libs tests
uv run isort services libs tests

# Lint
uv run ruff check services libs tests

# Type check
uv run mypy services libs

# Security scan
uv run bandit -r services libs

# Run tests
uv run pytest -v --cov=services
```

Or use the all-in-one command:

```bash
uv run black --check services libs tests && \
uv run isort --check services libs tests && \
uv run ruff check services libs tests && \
uv run mypy services libs && \
uv run pytest --cov=services --cov-fail-under=80
```

### 3. Commit Your Changes

```bash
git add .
git commit -m "feat: add new feature"  # See commit guidelines below
```

Pre-commit hooks will automatically run. Fix any issues before proceeding.

### 4. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Coding Standards

This project follows strict Python coding standards based on PEP 8, with additional requirements.

### Python Version

- Use Python 3.12+
- Leverage modern Python features (type hints, pattern matching, etc.)

### Formatting (Automated)

- **Black**: Line length 88, automatic formatting
- **isort**: Import sorting, Black-compatible profile
- Pre-commit hooks enforce formatting automatically

### Type Hints (Required)

All functions must have type hints:

```python
from typing import Any

def process_data(input_data: dict[str, Any], user_id: str) -> dict[str, Any]:
    """Process user data."""
    return {"result": "success"}
```

### Docstrings (Required)

Use Google-style docstrings for all public modules, classes, and functions:

```python
def create_player(username: str, email: str) -> PlayerAccount:
    """
    Create a new player account.

    Args:
        username: The player's username (3-30 characters)
        email: The player's email address

    Returns:
        PlayerAccount: The created player account object

    Raises:
        ConflictException: If username or email already exists
        ValidationException: If inputs are invalid

    Example:
        >>> player = create_player("john_doe", "john@example.com")
        >>> print(player.username)
        john_doe
    """
    # Implementation
```

### Naming Conventions

- **Modules**: `lowercase_with_underscores.py`
- **Classes**: `PascalCase`
- **Functions/methods**: `lowercase_with_underscores`
- **Constants**: `UPPERCASE_WITH_UNDERSCORES`
- **Private members**: `_leading_underscore`

### Pydantic Models

Use Pydantic for all data validation:

```python
from pydantic import BaseModel, Field, EmailStr

class CreatePlayerRequest(BaseModel):
    """Request model for creating a player."""

    username: str = Field(min_length=3, max_length=30, description="Username")
    email: EmailStr = Field(description="Email address")
    display_name: str | None = Field(default=None, description="Display name")
```

### Error Handling

Use custom exceptions from `libs.exceptions`:

```python
from libs.exceptions import ValidationException, NotFoundException

def get_player(player_id: str) -> PlayerAccount:
    """Get player by ID."""
    player = storage.get(player_id)
    if not player:
        raise NotFoundException(f"Player '{player_id}' not found")
    return player
```

### Logging

Use AWS Lambda Powertools logger:

```python
from libs.logger import get_logger

logger = get_logger(__name__)

def process_request(request_id: str) -> None:
    """Process a request."""
    logger.info("Processing request", extra={"request_id": request_id})
    try:
        # Process
        logger.info("Request processed successfully")
    except Exception as e:
        logger.error("Processing failed", extra={"error": str(e)})
        raise
```

**Never use `print()` statements** - always use the logger.

### Security Best Practices

1. **Never commit secrets**: Use environment variables or AWS Secrets Manager
2. **Validate all inputs**: Use Pydantic models
3. **Sanitize error messages**: Don't expose internal details
4. **Use parameterized queries**: Prevent injection attacks
5. **Follow least privilege**: Minimal IAM permissions

## Testing Requirements

### Test Coverage

- **Minimum coverage**: 80% overall
- **Critical paths**: 100% coverage for authentication, authorization
- All new code must include tests

### Test Types

#### 1. Unit Tests

Test individual functions and classes in isolation:

```python
import pytest
from services.idp_api.service import IDPService
from libs.exceptions import AuthenticationException

class TestIDPService:
    """Unit tests for IDP service."""

    def test_authenticate_valid_credentials(self) -> None:
        """Test authentication with valid credentials."""
        service = IDPService()
        token = service.authenticate("testuser", "password123")
        assert token.access_token is not None

    def test_authenticate_invalid_credentials(self) -> None:
        """Test authentication with invalid credentials."""
        service = IDPService()
        with pytest.raises(AuthenticationException):
            service.authenticate("testuser", "wrongpassword")
```

#### 2. Integration Tests

Test Lambda handlers end-to-end:

```python
import pytest
from unittest.mock import MagicMock

@pytest.mark.integration
class TestIDPAPIIntegration:
    """Integration tests for IDP API."""

    def test_full_authentication_flow(self, lambda_context: MagicMock) -> None:
        """Test complete authentication flow."""
        # Test handler with realistic event
        from services.idp_api.handler import lambda_handler

        event = {
            "httpMethod": "POST",
            "path": "/auth/token",
            "body": '{"username":"testuser","password":"password123"}'
        }

        response = lambda_handler(event, lambda_context)
        assert response["statusCode"] == 200
```

#### 3. End-to-End Tests

Test deployed infrastructure (in `tests/e2e/`):

```python
import pytest
import requests

@pytest.mark.e2e
def test_deployed_api(e2e_api_base_url: str) -> None:
    """Test deployed API endpoint."""
    response = requests.post(
        f"{e2e_api_base_url}/auth/token",
        json={"username": "testuser", "password": "password123"}
    )
    assert response.status_code == 200
```

### Running Tests

```bash
# All tests
uv run pytest -v

# Unit tests only
uv run pytest -v -m unit

# Integration tests
uv run pytest -v -m integration

# E2E tests (requires deployed infrastructure)
E2E_API_BASE_URL=https://your-api.execute-api.us-east-1.amazonaws.com \
uv run pytest tests/e2e/ -m e2e -v

# With coverage
uv run pytest --cov=services --cov-report=html
```

### Test Fixtures

Use pytest fixtures for reusable test setup:

```python
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def lambda_context() -> MagicMock:
    """Create mock Lambda context."""
    context = MagicMock()
    context.request_id = "test-request-id"
    context.function_name = "test-function"
    return context

@pytest.fixture
def sample_player() -> PlayerAccount:
    """Create sample player for testing."""
    return PlayerAccount(
        player_id="plr_test",
        username="testplayer",
        email="test@example.com"
    )
```

## Pull Request Process

### Before Submitting

1. ✅ All tests pass
2. ✅ Code coverage is ≥80%
3. ✅ All quality checks pass (black, ruff, mypy, bandit)
4. ✅ Documentation is updated
5. ✅ CHANGELOG is updated (if applicable)
6. ✅ Commit messages follow guidelines

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project coding standards
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally
- [ ] Dependent changes merged and published
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs automatically
2. **Code Review**: At least one approval required
3. **Address Feedback**: Make requested changes
4. **Merge**: Squash and merge when approved

### Review Checklist (for Reviewers)

- [ ] Code implements stated requirements
- [ ] Design is maintainable and follows patterns
- [ ] Tests cover new logic and edge cases
- [ ] Type hints are present and correct
- [ ] Documentation is clear and complete
- [ ] No security vulnerabilities introduced
- [ ] Performance considerations addressed
- [ ] Error handling is appropriate
- [ ] Logging is adequate
- [ ] CI passes all checks

## Commit Message Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/):

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks
- **perf**: Performance improvements
- **ci**: CI/CD changes

### Examples

```bash
# Simple feature
git commit -m "feat: add player statistics endpoint"

# Bug fix with scope
git commit -m "fix(idp-api): correct token expiration validation"

# Breaking change
git commit -m "feat!: change authentication flow

BREAKING CHANGE: Authentication now requires email instead of username"

# With detailed description
git commit -m "refactor(player-api): improve error handling

- Add custom exception classes
- Update error response format
- Add error logging

Closes #123"
```

### Commit Message Rules

1. **Subject line**:
   - Max 50 characters
   - Start with lowercase
   - No period at end
   - Imperative mood ("add" not "added")

2. **Body** (optional):
   - Wrap at 72 characters
   - Explain what and why, not how
   - Separate from subject with blank line

3. **Footer** (optional):
   - Reference issues: `Closes #123`
   - Note breaking changes: `BREAKING CHANGE: description`

## Adding a New Lambda Function

Follow this pattern when adding a new Lambda:

### 1. Create Directory Structure

```bash
mkdir -p services/new_api/{tests,}
touch services/new_api/{__init__.py,handler.py,service.py,models.py}
touch services/new_api/tests/{__init__.py,test_handler.py,test_service.py,test_integration.py}
```

### 2. Implement Lambda

- **models.py**: Pydantic request/response models
- **service.py**: Business logic
- **handler.py**: Lambda handler with routing
- **tests/**: Unit and integration tests

### 3. Update Terraform

Add Lambda function in `infra/terraform/lambda.tf`:

```hcl
resource "aws_lambda_function" "new_api" {
  filename         = data.archive_file.new_api_lambda.output_path
  function_name    = "${var.project_name}-${var.environment}-new-api"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "services.new_api.handler.lambda_handler"
  runtime         = var.lambda_runtime
  # ...
}
```

Add API Gateway routes in `infra/terraform/api_gateway.tf`:

```hcl
resource "aws_apigatewayv2_route" "new_api_route" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /new-endpoint"
  target    = "integrations/${aws_apigatewayv2_integration.new_api.id}"
}
```

### 4. Update Documentation

- Update README.md with new endpoints
- Update API documentation section
- Add to CHANGELOG.md

## Project Maintenance

### Dependency Updates

```bash
# Update dependencies
uv sync --upgrade

# Test after updates
uv run pytest -v

# Commit lock file
git add uv.lock
git commit -m "chore: update dependencies"
```

### Pre-commit Hook Updates

```bash
# Update pre-commit hooks
uv run pre-commit autoupdate

# Test hooks
uv run pre-commit run --all-files
```

## Getting Help

- **Documentation**: Check README.md and code comments
- **Issues**: Search existing issues on GitHub
- **Discussions**: Start a discussion for questions
- **Code Examples**: Look at existing Lambda implementations

## Recognition

Contributors will be recognized in:
- CHANGELOG.md for significant features
- Project README (Contributors section)
- Release notes

## Questions?

If you have questions about contributing, please:
1. Check this document
2. Review existing code examples
3. Create a discussion on GitHub
4. Ask in pull request comments

Thank you for contributing to the PSN Partner Emulator! 🚀
