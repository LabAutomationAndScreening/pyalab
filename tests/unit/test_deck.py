import pytest

from pyalab import Deck
from pyalab import DeckPosition
from pyalab import DeckPositionNotFoundError
from pyalab import Labware
from pyalab import LabwareOrientation
from pyalab import Plate
from pyalab import StandardDeckNames

from .constants import GENERIC_96_WELL_PLATE
from .constants import GENERIC_RESERVOIR
from .constants import GENERIC_TUBE_HOLDER


class TestDeckPositionSectionIndex:
    @pytest.mark.parametrize(
        ("deck_name", "deck_position", "labware", "expected"),
        [
            pytest.param(
                StandardDeckNames.THREE_POSITION.value,
                DeckPosition(name="A", orientation=LabwareOrientation.A1_NW_CORNER),
                GENERIC_RESERVOIR,
                2,
                id="3 position deck, A position reservoir",
            ),
            pytest.param(
                StandardDeckNames.THREE_POSITION.value,
                DeckPosition(name="B", orientation=LabwareOrientation.A1_NW_CORNER),
                GENERIC_96_WELL_PLATE,
                6,
                id="3 position deck, B plate landscape",
            ),
            pytest.param(
                StandardDeckNames.THREE_POSITION.value,
                DeckPosition(name="B", orientation=LabwareOrientation.A1_NE_CORNER),
                GENERIC_96_WELL_PLATE,
                6,
                id="3 position deck, B plate portrait",
            ),
            pytest.param(
                StandardDeckNames.THREE_POSITION.value,
                DeckPosition(name="C", orientation=LabwareOrientation.A1_NW_CORNER),
                Plate(name="4TITUDE 384 Well Skirted PCR Plate 55 µl"),  # arbitrary SBS footprint
                14,
                id="3 position deck, C plate landscape",
            ),
            pytest.param(
                StandardDeckNames.THREE_POSITION.value,
                DeckPosition(name="C", orientation=LabwareOrientation.A1_NW_CORNER),
                GENERIC_TUBE_HOLDER,
                13,
                id="3 position deck, C tubeholder",
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
        deck_position = DeckPosition(name="B", orientation=LabwareOrientation.A1_NW_CORNER)
        arbitrary_incompatible_labware = GENERIC_RESERVOIR

        with pytest.raises(
            DeckPositionNotFoundError,
            match=rf"{deck.name}.*{deck_position.name}.*{arbitrary_incompatible_labware.xml_width}.*{arbitrary_incompatible_labware.xml_length}",
        ):
            _ = deck_position.section_index(deck=deck, labware=arbitrary_incompatible_labware)
