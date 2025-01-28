import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from pyalab import Deck
from pyalab import DeckLayout
from pyalab import DeckPosition
from pyalab import Labware
from pyalab import LabwareNotInDeckLayoutError
from pyalab import LabwareOrientation
from pyalab import Pipette
from pyalab import Plate
from pyalab import Program
from pyalab import Reservoir
from pyalab import StandardDeckNames
from pyalab import Tip
from pyalab import Tubeholder

from .constants import GENERIC_TUBE_HOLDER
from .fixtures import ProgramSnapshot


def test_Given_plate_not_on_deck__When_get_section_index_for_plate__Then_error():
    other_plate = Plate(name="BIO-RAD Hard-Shell 96-Well Skirted PCR Plates", display_name="not my plate")
    program = Program(
        deck_layouts=[
            DeckLayout(
                deck=Deck(name=StandardDeckNames.THREE_POSITION.value),
                labware={DeckPosition(name="B", orientation=LabwareOrientation.A1_NW_CORNER): other_plate},
            )
        ],
        display_name="arbitrary",
        description="arbitrary",
        pipette=Pipette(name="VOYAGER EIGHT 300 µl"),  # arbitrary
        tip=Tip(name="300 µl GripTip Sterile Filter Low retention"),  # arbitrary
    )
    desired_plate = Plate(name="BIO-RAD Hard-Shell 96-Well Skirted PCR Plates", display_name="PCR Plate")

    with pytest.raises(LabwareNotInDeckLayoutError, match=rf"{desired_plate.name}.*{desired_plate.display_name}"):
        _ = program.get_section_index_for_labware(desired_plate)


class TestOddLabwareProgramSnapshots(ProgramSnapshot):
    @pytest.mark.parametrize(
        (
            "position_a_labware",
            "position_b_labware",
            "position_b_orientation",
            "position_c_labware",
            "position_c_orientation",
        ),
        [
            pytest.param(
                Reservoir(name="INTEGRA 10 ml Multichannel Reservoir"),
                GENERIC_TUBE_HOLDER,
                LabwareOrientation.A1_NW_CORNER,
                Reservoir(name="INTEGRA 12 Column Polypropylene Reservoir"),
                LabwareOrientation.A1_NW_CORNER,
                id="arbitrary1",
            ),
            pytest.param(
                Reservoir(name="INTEGRA 8 Row Polypropylene Reservoir"),
                Tubeholder(name="Rack for 15 ml centrifuge tubes"),
                LabwareOrientation.A1_NE_CORNER,
                GENERIC_TUBE_HOLDER,
                LabwareOrientation.A1_NW_CORNER,
                id="arbitrary2",
            ),
            pytest.param(
                None,
                Plate(name="INTEGRA 96 Deepwell V-Bottom Plate", display_name="fooBAR 173"),
                LabwareOrientation.A1_NE_CORNER,
                None,
                None,
                id="portrait-in-b",
            ),
        ],
    )
    def test_arbitrary_params(
        self,
        position_a_labware: Labware | None,
        position_b_labware: Labware | None,
        position_b_orientation: LabwareOrientation | None,
        position_c_labware: Labware | None,
        position_c_orientation: LabwareOrientation | None,
    ):
        labware_dict: dict[DeckPosition, Labware] = {}
        if position_a_labware is not None:
            labware_dict[DeckPosition(name="A", orientation=LabwareOrientation.A1_NW_CORNER)] = position_a_labware
        if position_b_labware is not None:
            assert position_b_orientation is not None
            labware_dict[DeckPosition(name="B", orientation=position_b_orientation)] = position_b_labware
        if position_c_labware is not None:
            assert position_c_orientation is not None
            labware_dict[DeckPosition(name="C", orientation=position_c_orientation)] = position_c_labware
        program = Program(
            deck_layouts=[
                DeckLayout(
                    deck=Deck(name=StandardDeckNames.THREE_POSITION.value),
                    labware=labware_dict,
                )
            ],
            display_name="arbitrary",
            description="arbitrary description",
            pipette=Pipette(name="VIAFLO TWELVE 1250 µl"),  # arbitrary
            tip=Tip(name="1250 µl GripTip Sterile Filter Low retention"),  # arbitrary
        )

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / f"{uuid.uuid1()}.iaa"
            program.dump_xml(file_path)
            xml_str = file_path.read_text()

        assert xml_str == self.snapshot_xml
