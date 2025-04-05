import random
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from syrupy.assertion import SnapshotAssertion

from pyalab import Deck
from pyalab import DeckLayout
from pyalab import DeckPosition
from pyalab import DOneTips
from pyalab import LabwareOrientation
from pyalab import Pipette
from pyalab import Plate
from pyalab import Program
from pyalab import StandardDeckNames
from pyalab import Tip


class ProgramSnapshot:
    @pytest.fixture(autouse=True)
    def _setup(self, snapshot_xml: SnapshotAssertion):
        self.snapshot_xml = snapshot_xml


def generate_xml_str(program: Program) -> str:
    with TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / f"{uuid.uuid1()}.iaa"
        program.save_program(file_path)
        return file_path.read_text()


ARBITRARY_D_ONE_PIPETTE = Pipette(name="VIAFLO SINGLE 300 µl")


def pick_random_d_one_pipette() -> Pipette:
    return Pipette(name=random.choice(("VIAFLO SINGLE 300 µl", "VIAFLO SINGLE 1250 µl")))


def arbitrary_d_one_program_framework() -> Program:
    pcr_plate = Plate(name="BIO-RAD Hard-Shell 96-Well Skirted PCR Plates", display_name="PCR Plate")
    return Program(
        display_name="arbitrary-display-name",
        deck_layouts=[
            DeckLayout(
                deck=Deck(name=StandardDeckNames.THREE_POSITION.value),
                labware={DeckPosition(name="B", orientation=LabwareOrientation.A1_NW_CORNER): pcr_plate},
            )
        ],
        description="foobar description",
        pipette=ARBITRARY_D_ONE_PIPETTE,
        tip=DOneTips(
            position_2=Tip(name="300 µl GripTip Sterile Filter"),
        ),
    )
