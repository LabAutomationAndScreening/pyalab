import uuid
from functools import cached_property
from typing import override

from lxml import etree
from lxml.etree import _Element
from pydantic import Field

from .integra_xml import LibraryComponent
from .integra_xml import LibraryComponentType


class Plate(LibraryComponent, frozen=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    type = LibraryComponentType.PLATE
    display_name: str = ""  # TODO: If left as blank, then set the display name to the name of the plate type # TODO: validate length and character class requirements

    @override
    def create_xml_for_program(self) -> _Element:
        root = super().create_xml_for_program()
        etree.SubElement(
            root, "NameInProcess"
        ).text = f"{self.display_name}!1"  # TODO: figure out why they all end in `!1`
        return root

    @cached_property
    def row_spacing(self) -> float:
        root = self.load_xml()
        row_gap_node = root.find(".//RowGap")
        assert row_gap_node is not None
        row_gap_text = row_gap_node.text
        assert row_gap_text is not None
        return float(row_gap_text) / 100  # in the XML the distance is in 0.01 mm units, but our standard is mm
