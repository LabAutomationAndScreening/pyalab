import random

import pytest
from pydantic import ValidationError

from pyalab import Deck
from pyalab import DeckLayout
from pyalab import DeckPosition
from pyalab import Labware
from pyalab import LabwareOrientation
from pyalab import Pipette
from pyalab import Plate
from pyalab import Program
from pyalab import SetInitialVolume
from pyalab import SetVolume
from pyalab import StandardDeckNames
from pyalab import Tip

from ..constants import GENERIC_RESERVOIR
from ..fixtures import ProgramSnapshot
from ..fixtures import generate_xml_str


class TestDataValidation:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.generic_plate = Plate(name="BIO-RAD Hard-Shell 96-Well Skirted PCR Plates")

    def test_When_negative_volume__Then_error(self):
        expected_volume = -0.1

        with pytest.raises(ValidationError, match=rf"volume(.|\n)*greater(.|\n)*{expected_volume}"):
            _ = SetVolume(labware=self.generic_plate, column_index=random.randint(0, 11), volume=expected_volume)


class TestDifferentLabwareProgramSnapshots(ProgramSnapshot):
    @pytest.mark.parametrize(
        ("labware", "deck", "deck_position", "pipette_span"),
        [
            pytest.param(
                GENERIC_RESERVOIR,
                Deck(name=StandardDeckNames.THREE_POSITION.value),
                DeckPosition(name="A", orientation=LabwareOrientation.A1_NW_CORNER),
                9,
                id="single well reservoir",
            ),
            pytest.param(
                GENERIC_RESERVOIR,
                Deck(name=StandardDeckNames.THREE_POSITION.value),
                DeckPosition(name="A", orientation=LabwareOrientation.A1_NW_CORNER),
                4.5,
                id="single well reservoir, unusual pipette span",
            ),
        ],
    )
    def test_arbitrary_params(
        self, labware: Labware, deck: Deck, deck_position: DeckPosition, pipette_span: float | None
    ):
        program = Program(
            deck_layouts=[
                DeckLayout(
                    deck=deck,
                    labware={deck_position: labware},
                )
            ],
            display_name="arbitrary",
            description="arbitrary description",
            pipette=Pipette(name="VOYAGER EIGHT 300 µl"),
            tip=Tip(name="300 µl GripTip Sterile Filter Low retention"),
        )
        labware_section_index = program.get_section_index_for_labware(labware)

        program.add_step(
            SetInitialVolume(
                labware=labware,
                section_index=labware_section_index,
                column_index=0,
                volume=150,
                pipette_span=pipette_span,
            )
        )
        program.add_step(
            SetVolume(
                labware=labware,
                section_index=labware_section_index,
                column_index=0,
                volume=140,
                pipette_span=pipette_span,
            )
        )

        assert generate_xml_str(program) == self.snapshot_xml
