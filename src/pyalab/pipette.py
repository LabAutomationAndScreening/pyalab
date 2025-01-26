from functools import cached_property

from .integra_xml import LibraryComponent
from .integra_xml import LibraryComponentType
from .integra_xml import hundredths_mm_to_mm


class Pipette(LibraryComponent, frozen=True):
    type = LibraryComponentType.PIPETTE
    name: str

    @cached_property
    def min_spacing(self) -> float:
        return hundredths_mm_to_mm(self._extract_xml_node_text("MinSpacing"))


class Tip(LibraryComponent, frozen=True):
    type = LibraryComponentType.TIP
    name: str

    @cached_property
    def tip_id(self) -> int:
        return int(self._extract_xml_node_text("TipID"))
