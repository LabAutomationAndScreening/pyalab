import re
from enum import Enum
from pathlib import Path
from typing import ClassVar

from lxml import etree
from lxml.etree import _Element
from pydantic import BaseModel

from .constants import PATH_TO_INCLUDED_XML_FILES

NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"


def hundredths_mm_to_mm(hundredths_mm: int | str) -> float:
    # the XML encodes the dimension in units of 0.01 mm, but our standard units are in mm.
    return float(hundredths_mm) / 100


class LibraryComponentType(Enum):
    # the string value should match the folder name within the Integra XML library
    DECK = "Deck"
    PLATE = "Plate"
    RESERVOIR = "Reservoir"
    PIPETTE = "Pipette"
    TIP = "Tip"
    TUBEHOLDER = "Tubeholder"


class IntegraLibraryObjectNotFoundError(OSError):
    def __init__(self, *, component_type: LibraryComponentType, name: str, paths_searched: list[Path]):
        self.type = component_type
        self.name = name
        super().__init__(f"Could not find {component_type.value} with name {name} while looking in {paths_searched}")


CONTENT_VERSIONS: dict[LibraryComponentType, str] = {
    LibraryComponentType.PLATE: "1",
    LibraryComponentType.RESERVOIR: "2",
    LibraryComponentType.TUBEHOLDER: "1",
}


class LibraryComponent(BaseModel, frozen=True):
    type: ClassVar[LibraryComponentType]
    name: str
    xml_file_version: str | None = None

    def load_xml(self) -> _Element:
        directory = PATH_TO_INCLUDED_XML_FILES / self.type.value
        xml_files = directory.glob("*.xml")
        regex_pattern = re.compile(rf"{self.name}\ V\d+\.xml")
        matched_files = [file for file in xml_files if regex_pattern.match(file.name)]
        if len(matched_files) == 0:
            raise IntegraLibraryObjectNotFoundError(
                component_type=self.type, name=self.name, paths_searched=[directory]
            )

        assert len(matched_files) == 1  # TODO: handle multiple versions in the library...
        file = matched_files[0]
        parser = etree.XMLParser(no_network=True, recover=False)
        tree = etree.parse(file, parser)
        root = tree.getroot()
        assert isinstance(root, _Element), f"Expected root to be an Element, but got type {type(root)} for {root}"
        return root

    def create_xml_for_program(self) -> _Element:
        is_content = self.type in CONTENT_VERSIONS
        root = etree.Element(
            "Content"
            if is_content
            else self.type.value,  # TODO: confirm that all object types use the file directory as the XML tag name too
            Version=str(1) if not is_content else CONTENT_VERSIONS[self.type],
        )
        if is_content:
            root.set(
                etree.QName(NS_XSI, "type"),
                self.type.value,  # TODO: confirm that all object types use the file directory as the xsi:type too
            )

        for subelement in self.load_xml():
            root.append(subelement)
        return root

    def _extract_xml_node_text(self, node_name: str) -> str:
        root = self.load_xml()
        node = root.find(f".//{node_name}")
        assert node is not None
        text = node.text
        assert text is not None
        return text
