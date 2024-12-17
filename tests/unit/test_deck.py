import pytest

from pyalab import Deck
from pyalab import DeckPosition
from pyalab import DeckPositionNotFoundError
from pyalab import DeckPositions
from pyalab import StandardDeckNames


class TestDeckPositionSectionIndex:
    @pytest.mark.parametrize(
        ("deck_name", "deck_position", "expected"),
        [
            pytest.param(
                StandardDeckNames.THREE_POSITION.value,
                DeckPositions.B_PLATE_LANDSCAPE.value,
                6,
                id="3 position deck, B plate landscape",
            ),
            pytest.param(
                StandardDeckNames.THREE_POSITION.value,
                DeckPositions.C_PLATE_LANDSCAPE.value,
                14,
                id="3 position deck, C plate landscape",
            ),
        ],
    )
    def test_Given_match__Then_finds_it(self, deck_name: str, deck_position: DeckPosition, expected: int):
        deck = Deck(name=deck_name)

        actual = deck_position.section_index(deck)

        assert actual == expected

    def test_Given_no_match__Then_error(self):
        deck = Deck(name=StandardDeckNames.FOUR_POSITION.value)
        deck_position = DeckPositions.B_PLATE_LANDSCAPE.value

        with pytest.raises(
            DeckPositionNotFoundError,
            match=rf"{deck.name}.*{deck_position.name}.*{deck_position.xml_width}.*{deck_position.xml_length}",
        ):
            _ = deck_position.section_index(deck)
