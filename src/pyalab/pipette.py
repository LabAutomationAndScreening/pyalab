from functools import cached_property

from pydantic import BaseModel

from .integra_xml import LibraryComponent
from .integra_xml import LibraryComponentType
from .integra_xml import hundredths_mm_to_mm


class Pipette(LibraryComponent, frozen=True):
    type = LibraryComponentType.PIPETTE
    name: str

    @cached_property
    def min_spacing(self) -> float:
        return hundredths_mm_to_mm(self._extract_xml_node_text("MinSpacing"))

    @cached_property
    def num_channels(self) -> int:
        return int(self._extract_xml_node_text("Channels"))

    @cached_property
    def is_d_one(self) -> bool:
        return self.num_channels == 1


class Tip(LibraryComponent, frozen=True):
    type = LibraryComponentType.TIP
    name: str

    @cached_property
    def tip_id(self) -> int:
        return int(self._extract_xml_node_text("TipID"))


class DOneTips(BaseModel, frozen=True):
    # TODO: require at least one tip position not be None
    position_1: Tip | None = None
    position_2: Tip | None = None
