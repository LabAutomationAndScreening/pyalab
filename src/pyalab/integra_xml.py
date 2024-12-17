import re
from enum import Enum
from pathlib import Path
from xml.etree.ElementTree import Element

from lxml import etree
from pydantic import BaseModel

from .constants import PATH_TO_INCLUDED_XML_FILES


class LibraryComponentType(Enum):
    DECK = "Deck"
    PLATE = "Plate"


class IntegraLibraryObjectNotFoundError(OSError):
    def __init__(self, *, component_type: LibraryComponentType, name: str, paths_searched: list[Path]):
        self.type = component_type
        self.name = name
        super().__init__(f"Could not find {component_type.value} with name {name} while looking in {paths_searched}")


class LibraryComponent(BaseModel):
    type: LibraryComponentType
    name: str
    xml_file_version: str | None = None
    _xml_root: Element | None = None

    def load_xml(self) -> None:
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
        tree = etree.parse(file, parser)  # noqa: S320 # using this custom parser should mitigate security concerns about untrusted XML files. And defusedxml is end of life anyway
        root = tree.getroot()
        assert isinstance(root, Element), f"Expected root to be an Element, but got type {type(root)} for {root}"
        self._xml_root = root

    @property
    def xml_root(self) -> Element:
        assert isinstance(self._xml_root, Element)
        return self._xml_root
