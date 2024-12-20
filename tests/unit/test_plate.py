import pytest

from pyalab import Plate


class TestTip:
    @pytest.mark.parametrize(
        ("name", "expected"),
        [("BIO-RAD Hard-Shell 96-Well Skirted PCR Plates", 9), ("4TITUDE 384 Well Skirted PCR Plate 55 µl", 4.5)],
    )
    def test_row_spacing(self, name: str, expected: int):
        plate = Plate(name=name)

        actual = plate.row_spacing

        assert actual == expected
