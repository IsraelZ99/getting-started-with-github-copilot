"""
Shared test configuration and fixtures for the FastAPI application tests.
"""

import pytest
from fastapi.testclient import TestClient
from app import app, activities


@pytest.fixture(scope="session")
def fastapi_app():
    """
    Provide the FastAPI app instance for the test session.
    """
    return app


@pytest.fixture(scope="function")
def client(fastapi_app):
    """
    Provide a TestClient instance for making HTTP requests.
    Scope is function-level to ensure isolation between tests.
    """
    return TestClient(fastapi_app)


@pytest.fixture(scope="function")
def sample_activities():
    """
    Reset the in-memory activities database to a known state before each test.
    Ensures test isolation by providing a fresh copy of activities.
    """
    # Store original state
    original_activities = {
        activity: {
            "description": activity_data["description"],
            "schedule": activity_data["schedule"],
            "max_participants": activity_data["max_participants"],
            "participants": activity_data["participants"].copy(),
        }
        for activity, activity_data in activities.items()
    }

    # Yield to the test
    yield activities

    # Restore original state after test
    for activity, activity_data in original_activities.items():
        activities[activity] = activity_data
