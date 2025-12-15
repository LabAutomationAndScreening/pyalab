import logging

import pytest

from .snapshot import snapshot_xml  # noqa: F401 # this is a fixture we need in conftest scope

logger = logging.getLogger(__name__)


def pytest_configure(
    config: pytest.Config,  # noqa: ARG001 # the config argument MUST be present (even when unused) or pytest throws an error
):
    # force the vcr.cassette logger to WARNING+ because otherwise the logs get super noisy with the playback of all the cassettes
    vcr_logger = logging.getLogger("vcr.cassette")
    vcr_logger.setLevel(logging.WARNING)
