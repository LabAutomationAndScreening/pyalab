import pytest
from syrupy.assertion import SnapshotAssertion


class ProgramSnapshot:
    @pytest.fixture(autouse=True)
    def _setup(self, snapshot_xml: SnapshotAssertion):
        self.snapshot_xml = snapshot_xml
