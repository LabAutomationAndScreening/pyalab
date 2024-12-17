from pathlib import Path

from pyalab import Deck
from pyalab import DeckLayout
from pyalab import DeckPositions
from pyalab import Pipette
from pyalab import Plate
from pyalab import Program
from pyalab import StandardDeckNames
from pyalab import Tip


def test_simple_transfer_program_matches_snapshot():
    program = Program(
        deck_layouts=[
            DeckLayout(
                deck=Deck(name=StandardDeckNames.THREE_POSITION.value),
                labware={
                    DeckPositions.B_PLATE_LANDSCAPE.value: Plate(
                        name="BIO-RAD Hard-Shell 96-Well Skirted PCR Plates", display_name="PCR Plate"
                    )
                },
            )
        ],
        display_name="simple-transfer",
        description="One transfer within a 96-well plate",
        pipette=Pipette(name="VOYAGER EIGHT 300 µl"),
        tip=Tip(name="300 µl GripTip Sterile Filter Low retention"),
    )

    program.dump_xml(Path(__file__).parent / "simple_transfer_program.xml")
