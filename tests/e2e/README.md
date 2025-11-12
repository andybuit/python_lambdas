# End-to-End Tests

This directory contains end-to-end tests for the PSN Partner Emulator service.

## Overview

E2E tests validate the entire system including:
- Multiple Lambda functions working together
- API Gateway integration
- DynamoDB interactions (when deployed)
- Authentication flows across services
- Real AWS infrastructure (in test environment)

## Test Structure

```
tests/e2e/
├── README.md              # This file
├── conftest.py           # Pytest fixtures for E2E tests
├── test_idp_flow.py      # IDP API E2E tests
├── test_player_flow.py   # Player Account API E2E tests
└── test_cross_service.py # Cross-service integration tests
```

## Setup

### Prerequisites

1. AWS credentials configured with access to test environment
2. Terraform deployed infrastructure in test environment
3. Python dependencies installed:
   ```bash
   # From project root
   uv sync

   # Activate virtual environment
   # On Windows:
   .venv\Scripts\activate
   # On Linux/macOS:
   source .venv/bin/activate

   # Note: Each service has its own pyproject.toml with specific dependencies
   ```

### Configuration

Set environment variables for E2E tests:

```bash
export E2E_API_BASE_URL=https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com
export E2E_AWS_REGION=us-east-1
export E2E_TEST_ENVIRONMENT=test
```

## Running E2E Tests

### Run all E2E tests:
```bash
uv run pytest tests/e2e/ -m e2e -v
```

### Run specific E2E test file:
```bash
uv run pytest tests/e2e/test_idp_flow.py -v
```

### Run with detailed output:
```bash
uv run pytest tests/e2e/ -m e2e -v -s
```

## Test Data Cleanup

E2E tests should clean up after themselves. The `conftest.py` includes fixtures for:
- Creating test users/players
- Cleaning up test data after tests complete
- Handling test isolation

## Framework Recommendations

Consider using these frameworks for E2E testing:

### Option 1: pytest + requests (Current)
- Simple and straightforward
- Good for API-level testing
- Built on existing pytest infrastructure

### Option 2: Tavern
- YAML-based API testing framework
- Built on pytest
- Good for REST API validation
- Install: `uv add --dev tavern`

### Option 3: Locust
- Load testing and E2E testing
- Can simulate multiple users
- Performance testing capabilities
- Install: `uv add --dev locust`

### Option 4: AWS SAM CLI Local Testing
- Test Lambda functions locally with sam local
- Simulate API Gateway locally
- Good for pre-deployment testing

## Best Practices

1. **Test Isolation**: Each test should be independent and not rely on other tests
2. **Cleanup**: Always clean up test data, even if tests fail
3. **Idempotency**: Tests should be repeatable without side effects
4. **Realistic Data**: Use realistic test data that mimics production scenarios
5. **Error Cases**: Test both happy paths and error scenarios
6. **Performance**: Monitor test execution time and optimize slow tests

## Example E2E Test

```python
import pytest
import requests

@pytest.mark.e2e
def test_full_user_journey(e2e_api_base_url, test_user_credentials):
    \"\"\"Test complete user journey from login to player creation.\"\"\"
    # 1. Authenticate with IDP API
    auth_response = requests.post(
        f\"{e2e_api_base_url}/auth/token\",
        json=test_user_credentials
    )
    assert auth_response.status_code == 200
    token = auth_response.json()[\"access_token\"]

    # 2. Create player account
    headers = {\"Authorization\": f\"Bearer {token}\"}
    player_response = requests.post(
        f\"{e2e_api_base_url}/players\",
        json={\"username\": \"e2e_test\", \"email\": \"e2e@test.com\"},
        headers=headers
    )
    assert player_response.status_code == 201

    # 3. Verify player exists
    player_id = player_response.json()[\"player_id\"]
    get_response = requests.get(
        f\"{e2e_api_base_url}/players/{player_id}\",
        headers=headers
    )
    assert get_response.status_code == 200
```

## CI/CD Integration

E2E tests should run:
- After deployment to test environment
- Before promoting to production
- On a scheduled basis to catch regressions

See `.github/workflows/e2e-tests.yml` for CI configuration.
