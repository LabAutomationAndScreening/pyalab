import uuid
from functools import cached_property
from typing import override

from lxml import etree
from lxml.etree import _Element
from pydantic import Field

from .integra_xml import LibraryComponent
from .integra_xml import LibraryComponentType

MAX_SPAN_FOR_VOYAGER = 33  # the 4 channel can span this wide


class RowSpacingAboveLimitError(ValueError):
    def __init__(self, attempted_spacing: float):
        super().__init__(
            f"The attempted row spacing {attempted_spacing} is larger than any pipette can span. Likely there is a bug in the code and an explicit spacing was not provided to a reservoir that multiple pipettes can access at once."
        )


class Labware(LibraryComponent, frozen=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    display_name: str = ""  # TODO: If left as blank, then set the display name to the name of the plate type # TODO: validate length and character class requirements

    @override
    def create_xml_for_program(self) -> _Element:
        root = super().create_xml_for_program()
        etree.SubElement(
            root, "NameInProcess"
        ).text = f"{self.display_name}!1"  # TODO: figure out why they all end in `!1`
        return root

    def row_spacing(self) -> float:
        spacing = self.row_spacing_in_xml
        if spacing > MAX_SPAN_FOR_VOYAGER:
            raise RowSpacingAboveLimitError(spacing)
        return spacing

    @cached_property
    def row_spacing_in_xml(self) -> float:
        return (
            float(self._extract_xml_node_text("RowGap")) / 100
        )  # in the XML the distance is in 0.01 mm units, but our standard is mm

    @cached_property
    def length(self) -> float:
        # Length is the horizontal distance when object is in landscape orientation (rows A, B, C lined up vertically)
        return (
            float(self._extract_xml_node_text("FootprintLengthMM")) / 100
        )  # in the XML the distance is in 0.01 mm units, but our standard is mm

    @cached_property
    def width(self) -> float:
        # Width is the vertical (in ViaLab view...or back-to-front on the ASSIST Plus) distance when object is in landscape orientation (rows A, B, C lined up horizontally)
        # Non-SBS reservoirs (e.g. INTEGRA 10 ml Multichannel Reservoir in Slot A) are represented as always being in landscape orientation
        return (
            float(self._extract_xml_node_text("FootprintWidthMM")) / 100
        )  # in the XML the distance is in 0.01 mm units, but our standard is mm

    # the XML encodes the dimension in units of 0.01 mm, but our standard units are in mm. But sometimes these values are needed for XML matching/searching
    @cached_property
    def xml_width(self) -> int:
        return int(round(self.width * 100, 0))

    @cached_property
    def xml_length(self) -> int:
        return int(round(self.length * 100, 0))


class Plate(Labware, frozen=True):
    type = LibraryComponentType.PLATE


class Tubeholder(Labware, frozen=True):
    type = LibraryComponentType.TUBEHOLDER


class Reservoir(Labware, frozen=True):
    type = LibraryComponentType.RESERVOIR
