from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from syrupy.assertion import SnapshotAssertion

from pyalab import Deck
from pyalab import DeckLayout
from pyalab import DeckPositions
from pyalab import LabwareNotInDeckLayoutError
from pyalab import Pipette
from pyalab import Plate
from pyalab import Program
from pyalab import SetInitialVolume
from pyalab import StandardDeckNames
from pyalab import Tip
from pyalab import Transfer


def test_Given_plate_not_on_deck__When_get_section_index_for_plate__Then_error():
    other_plate = Plate(name="BIO-RAD Hard-Shell 96-Well Skirted PCR Plates", display_name="not my plate")
    program = Program(
        deck_layouts=[
            DeckLayout(
                deck=Deck(name=StandardDeckNames.THREE_POSITION.value),
                labware={DeckPositions.B_PLATE_LANDSCAPE.value: other_plate},
            )
        ],
        display_name="arbitrary",
        description="arbitrary",
        pipette=Pipette(name="VOYAGER EIGHT 300 µl"),  # arbitrary
        tip=Tip(name="300 µl GripTip Sterile Filter Low retention"),  # arbitrary
    )
    desired_plate = Plate(name="BIO-RAD Hard-Shell 96-Well Skirted PCR Plates", display_name="PCR Plate")

    with pytest.raises(LabwareNotInDeckLayoutError, match=rf"{desired_plate.name}.*{desired_plate.display_name}"):
        _ = program.get_section_index_for_plate(desired_plate)


def test_simple_transfer_program_matches_snapshot(snapshot_xml: SnapshotAssertion):
    source_column_index = 3  # arbitrary
    destination_column_index = 8
    pcr_plate = Plate(name="BIO-RAD Hard-Shell 96-Well Skirted PCR Plates", display_name="PCR Plate")
    program = Program(
        deck_layouts=[
            DeckLayout(
                deck=Deck(name=StandardDeckNames.THREE_POSITION.value),
                labware={DeckPositions.B_PLATE_LANDSCAPE.value: pcr_plate},
            )
        ],
        display_name="simple-transfer",
        description="One transfer within a 96-well plate",
        pipette=Pipette(name="VOYAGER EIGHT 300 µl"),
        tip=Tip(name="300 µl GripTip Sterile Filter Low retention"),
    )
    pcr_plate_section_index = program.get_section_index_for_plate(pcr_plate)

    program.add_step(
        SetInitialVolume(
            plate=pcr_plate, section_index=pcr_plate_section_index, column_index=source_column_index, volume=100
        )
    )
    program.add_step(
        SetInitialVolume(
            plate=pcr_plate, section_index=pcr_plate_section_index, column_index=destination_column_index, volume=0
        )
    )

    program.add_step(
        Transfer(
            source=pcr_plate,
            source_section_index=pcr_plate_section_index,
            source_column_index=source_column_index,
            destination=pcr_plate,
            destination_section_index=pcr_plate_section_index,
            destination_column_index=destination_column_index,
            volume=50,
        )
    )

    with TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / "simple_transfer_program.iaa"
        program.dump_xml(file_path)
        xml_str = file_path.read_text()

    assert xml_str == snapshot_xml
