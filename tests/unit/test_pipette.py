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

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("VOYAGER FOUR 300 µl", False),
            ("VOYAGER EIGHT 50 µl", False),
            ("VIAFLO SINGLE 300 µl", True),
            ("VIAFLO SINGLE 1250 µl", True),
        ],
    )
    def test_is_d_one(self, name: str, expected: bool):
        pipette = Pipette(name=name)

        actual = pipette.is_d_one

        assert actual is expected

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("VOYAGER FOUR 300 µl", 4),
            ("VOYAGER EIGHT 50 µl", 8),
            ("VIAFLO SINGLE 300 µl", 1),
            ("VIAFLO SINGLE 1250 µl", 1),
        ],
    )
    def test_num_channels(self, name: str, expected: int):
        pipette = Pipette(name=name)

        actual = pipette.num_channels

        assert actual is expected
