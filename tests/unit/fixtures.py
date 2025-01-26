import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from syrupy.assertion import SnapshotAssertion

from pyalab import Program


class ProgramSnapshot:
    @pytest.fixture(autouse=True)
    def _setup(self, snapshot_xml: SnapshotAssertion):
        self.snapshot_xml = snapshot_xml


def generate_xml_str(program: Program) -> str:
    with TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / f"{uuid.uuid1()}.iaa"
        program.dump_xml(file_path)
        return file_path.read_text()
