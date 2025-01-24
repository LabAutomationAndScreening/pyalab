import pytest

from pyalab import Deck
from pyalab import DeckPosition
from pyalab import DeckPositionNotFoundError
from pyalab import Labware
from pyalab import LabwareOrientation
from pyalab import Plate
from pyalab import Reservoir
from pyalab import StandardDeckNames


class TestDeckPositionSectionIndex:
    @pytest.mark.parametrize(
        ("deck_name", "deck_position", "labware", "expected"),
        [
            pytest.param(
                StandardDeckNames.THREE_POSITION.value,
                DeckPosition(name="B", orientation=LabwareOrientation.LANDSCAPE),
                Plate(name="BIO-RAD Hard-Shell 96-Well Skirted PCR Plates"),  # arbitrary SBS footprint
                6,
                id="3 position deck, B plate landscape",
            ),
            pytest.param(
                StandardDeckNames.THREE_POSITION.value,
                DeckPosition(name="C", orientation=LabwareOrientation.LANDSCAPE),
                Plate(name="4TITUDE 384 Well Skirted PCR Plate 55 µl"),  # arbitrary SBS footprint
                14,
                id="3 position deck, C plate landscape",
            ),
        ],
    )
    def test_Given_match__Then_finds_it(
        self, deck_name: str, deck_position: DeckPosition, labware: Labware, expected: int
    ):
        deck = Deck(name=deck_name)

        actual = deck_position.section_index(deck=deck, labware=labware)

        assert actual == expected

    def test_Given_no_match__Then_error(self):
        deck = Deck(name=StandardDeckNames.FOUR_POSITION.value)
        deck_position = DeckPosition(name="B", orientation=LabwareOrientation.LANDSCAPE)
        arbitrary_labware = Reservoir(name="INTEGRA 10 ml Multichannel Reservoir")

        with pytest.raises(
            DeckPositionNotFoundError,
            match=rf"{deck.name}.*{deck_position.name}.*{arbitrary_labware.xml_width}.*{arbitrary_labware.xml_length}",
        ):
            _ = deck_position.section_index(deck=deck, labware=arbitrary_labware)
