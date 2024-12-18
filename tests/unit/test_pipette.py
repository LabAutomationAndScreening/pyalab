import pytest

from pyalab import Tip


class TestTip:
    @pytest.mark.parametrize(
        ("name", "expected"),
        [("300 µl GripTip Sterile Filter Low retention", 23), ("1250 µl GripTip Sterile Filter", 30)],
    )
    def test_tip_id(self, name: str, expected: int):
        tip = Tip(name=name)

        actual = tip.tip_id

        assert actual == expected
