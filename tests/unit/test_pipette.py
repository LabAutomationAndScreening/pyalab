import pytest

from pyalab import Pipette
from pyalab import Tip


# TODO: make the list of pipettes being tested a static list and zip it with a list of the expected values
class TestTip:
    @pytest.mark.parametrize(
        ("name", "expected"),
        [("300 µl GripTip Sterile Filter Low retention", 23), ("1250 µl GripTip Sterile Filter", 30)],
    )
    def test_tip_id(self, name: str, expected: int):
        tip = Tip(name=name)

        actual = tip.tip_id

        assert actual == expected


class TestPipette:
    @pytest.mark.parametrize(
        ("name", "expected"),
        [("VOYAGER FOUR 300 µl", 9), ("VOYAGER EIGHT 50 µl", 4.5)],
    )
    def test_min_spacing(self, name: str, expected: int):
        pipette = Pipette(name=name)

        actual = pipette.min_spacing

        assert actual == expected
