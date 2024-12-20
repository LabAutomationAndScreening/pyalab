from functools import cached_property

from .integra_xml import LibraryComponent
from .integra_xml import LibraryComponentType


class Pipette(LibraryComponent, frozen=True):
    type = LibraryComponentType.PIPETTE
    name: str


class Tip(LibraryComponent, frozen=True):
    type = LibraryComponentType.TIP
    name: str

    @cached_property
    def tip_id(self) -> int:
        return int(self._extract_xml_node_text("TipID"))
