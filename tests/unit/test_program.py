from pathlib import Path

from pyalab import Deck
from pyalab import Program
from pyalab import StandardDeckNames


def test_simple_transfer_program_matches_snapshot():
    program = Program(deck=Deck(name=StandardDeckNames.THREE_POSITION.value))

    program.dump_xml(Path(__file__).parent / "simple_transfer_program.xml")
