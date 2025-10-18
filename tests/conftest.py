"""
Shared pytest fixtures for API testing.
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from routers.policies import policy_storage


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI application.
    """
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_policy_storage():
    """
    Clear policy storage before each test to ensure test isolation.
    """
    policy_storage.clear()
    yield
    policy_storage.clear()

