import pytest

from pyalab import Deck
from pyalab import DeckLayout
from pyalab import DOneTips
from pyalab import InvalidTipInputFormatError
from pyalab import Pipette
from pyalab import Program
from pyalab import StandardDeckNames
from pyalab import Tip

from ..fixtures import ProgramSnapshot
from ..fixtures import generate_xml_str
from ..fixtures import pick_random_d_one_pipette


def test_Given_d_one_pipette__When_creating_a_program_with_non_d_one_tip_specs__Then_error():
    with pytest.raises(InvalidTipInputFormatError, match="a D-ONE pipette"):
        _ = Program(
            deck_layouts=[DeckLayout(deck=Deck(name=StandardDeckNames.THREE_POSITION.value), labware={})],
            display_name="arbitrary",
            description="arbitrary",
            pipette=pick_random_d_one_pipette(),
            tip=Tip(name="300 µl GripTip Sterile Filter Low retention"),  # arbitrary
        )


def test_Given_non_d_one_pipette__When_creating_a_program_with_d_one_tip_specs__Then_error():
    with pytest.raises(InvalidTipInputFormatError, match="non-D-ONE pipette"):
        _ = Program(
            deck_layouts=[DeckLayout(deck=Deck(name=StandardDeckNames.THREE_POSITION.value), labware={})],
            display_name="arbitrary",
            description="arbitrary",
            pipette=Pipette(name="VOYAGER EIGHT 300 µl"),  # arbitrary
            tip=DOneTips(position_1=Tip(name="300 µl GripTip Sterile Filter Low retention")),  # arbitrary
        )


class TestTipLayoutSnapshots(ProgramSnapshot):
    @pytest.mark.parametrize(
        (
            "pipette",
            "tip_config",
        ),
        [
            pytest.param(
                Pipette(name="VIAFLO SINGLE 300 µl"),
                DOneTips(position_1=Tip(name="12.5 µl GripTip Sterile")),
                id="300-ul-position-1-only",
            ),
        ],
    )
    def test_arbitrary_params(
        self,
        pipette: Pipette,
        tip_config: DOneTips,
    ):
        program = Program(
            deck_layouts=[
                DeckLayout(
                    deck=Deck(name=StandardDeckNames.THREE_POSITION.value),
                    labware={},
                )
            ],
            display_name="arbitrary",
            description="arbitrary description",
            pipette=pipette,
            tip=tip_config,
        )

        xml_str = generate_xml_str(program)

        assert xml_str == self.snapshot_xml
