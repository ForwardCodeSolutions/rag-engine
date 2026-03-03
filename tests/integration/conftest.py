"""Auto-mark all integration tests with the 'integration' marker."""

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Add 'integration' marker to every test in this directory."""
    for item in items:
        if "/integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
