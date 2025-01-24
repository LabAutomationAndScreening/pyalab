import pytest

from pyalab import Labware
from pyalab import Plate
from pyalab import Tubeholder


class TestSpacing:
    @pytest.mark.parametrize(
        ("labware", "expected"),
        [
            (Plate(name="BIO-RAD Hard-Shell 96-Well Skirted PCR Plates"), 9),
            (Plate(name="4TITUDE 384 Well Skirted PCR Plate 55 µl"), 4.5),
            (Tubeholder(name="Rack for 1.5 ml microcentrifuge tubes"), 13.5),
        ],
    )
    def test_row_spacing(self, labware: Labware, expected: float):
        actual = labware.row_spacing

        assert actual == expected


class TestFootprint:
    @pytest.mark.parametrize(
        ("labware", "expected", "expected_xml"),
        [
            (Plate(name="BIO-RAD Hard-Shell 96-Well Skirted PCR Plates"), 85.48, 8548),
            (Plate(name="4TITUDE 384 Well Skirted PCR Plate 55 µl"), 85.48, 8548),
            (Tubeholder(name="Rack for 1.5 ml microcentrifuge tubes"), 143.2, 14320),
        ],
    )
    def test_width(self, labware: Labware, expected: float, expected_xml: int):
        actual = labware.width
        actual_xml = labware.xml_width

        assert actual == expected
        assert actual_xml == expected_xml

    @pytest.mark.parametrize(
        ("labware", "expected", "expected_xml"),
        [
            (Plate(name="BIO-RAD Hard-Shell 96-Well Skirted PCR Plates"), 127.76, 12776),
            (Plate(name="4TITUDE 384 Well Skirted PCR Plate 55 µl"), 127.76, 12776),
            (Tubeholder(name="Rack for 1.5 ml microcentrifuge tubes"), 128, 12800),
        ],
    )
    def test_length(self, labware: Labware, expected: float, expected_xml: int):
        actual = labware.length
        actual_xml = labware.xml_length

        assert actual == expected
        assert actual_xml == expected_xml
