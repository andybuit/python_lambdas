"""Pytest configuration and fixtures for E2E tests."""

import os

import pytest


@pytest.fixture(scope="session")
def e2e_api_base_url() -> str:
    """
    Get the base URL for E2E tests.

    Returns:
        str: API Gateway base URL
    """
    url = os.getenv("E2E_API_BASE_URL")
    if not url:
        pytest.skip("E2E_API_BASE_URL environment variable not set")
    return url


@pytest.fixture(scope="session")
def e2e_aws_region() -> str:
    """
    Get AWS region for E2E tests.

    Returns:
        str: AWS region
    """
    return os.getenv("E2E_AWS_REGION", "us-east-1")


@pytest.fixture
def test_user_credentials() -> dict[str, str]:
    """
    Get test user credentials.

    Returns:
        dict: Test user credentials
    """
    return {"username": "testuser", "password": "password123"}


@pytest.fixture
def cleanup_test_players() -> None:
    """Cleanup test players after test completion."""
    # Placeholder for cleanup logic
    # In production, this would delete test players from DynamoDB
    yield
    # Cleanup code here
