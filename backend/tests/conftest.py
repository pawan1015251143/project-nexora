import pytest
from app.main import app

@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    """
    Ensure that dependency overrides are cleared after every test.
    This prevents state leakage between tests and test modules.
    """
    yield
    app.dependency_overrides.clear()
