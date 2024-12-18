from pathlib import Path

from pyalab import Deck
from pyalab import DeckLayout
from pyalab import DeckPositions
from pyalab import Pipette
from pyalab import Plate
from pyalab import Program
from pyalab import SetInitialVolume
from pyalab import StandardDeckNames
from pyalab import Tip
from pyalab import Transfer


def test_simple_transfer_program_matches_snapshot():
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

    program.dump_xml(Path(__file__).parent / "simple_transfer_program.xml")
