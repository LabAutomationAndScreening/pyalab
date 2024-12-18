import uuid
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
