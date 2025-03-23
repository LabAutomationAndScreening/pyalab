import pytest

from pyalab import Deck
from pyalab import DeckLayout
from pyalab import InvalidTipInputFormatError
from pyalab import Program
from pyalab import StandardDeckNames
from pyalab import Tip

from ..fixtures import pick_random_d_one_pipette


def test_When_creating_a_program_with_non_d_one_tip_specs__Then_error():
    with pytest.raises(InvalidTipInputFormatError):  # noqa: PT011 # there's no specific message within this error to match against, we're using a subclassed error to be specific
        _ = Program(
            deck_layouts=[DeckLayout(deck=Deck(name=StandardDeckNames.THREE_POSITION.value), labware={})],
            display_name="arbitrary",
            description="arbitrary",
            pipette=pick_random_d_one_pipette(),
            tip=Tip(name="300 µl GripTip Sterile Filter Low retention"),  # arbitrary
        )
