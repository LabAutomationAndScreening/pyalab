import logging

import pytest

from .snapshot import snapshot_xml  # noqa: F401 # this is a fixture we need in conftest scope

logger = logging.getLogger(__name__)


def pytest_configure(
    config: pytest.Config,
):
    """Configure pytest itself, such as logging levels."""
