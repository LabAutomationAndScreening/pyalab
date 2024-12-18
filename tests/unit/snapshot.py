from syrupy.extensions.single_file import SingleFileSnapshotExtension, WriteMode
import pytest, uuid

from syrupy.assertion import SnapshotAssertion
from pytest_mock import MockerFixture
from faker import Faker


class SingleFileXmlSnapshot(SingleFileSnapshotExtension):
    _write_mode = (
        WriteMode.TEXT
    )  # for some reason the default is binary, but it should be text to make diffs easier to read
    _file_extension = "xml"


@pytest.fixture
def snapshot_xml(snapshot: SnapshotAssertion, mocker: MockerFixture) -> SnapshotAssertion:
    _ = mocker.patch.object(  # TODO: consider switching to Faker https://stackoverflow.com/questions/41186818/how-to-generate-a-random-uuid-which-is-reproducible-with-a-seed-in-python
        uuid, "uuid4", side_effect=[uuid.UUID(f"00000000-0000-0000-0000-{str(i).zfill(12)}") for i in range(1000)]
    )
    return snapshot.use_extension(SingleFileXmlSnapshot)
