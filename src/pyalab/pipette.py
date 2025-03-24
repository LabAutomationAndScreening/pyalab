from functools import cached_property
from typing import override

from lxml.etree import _Element
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

    @override
    def load_xml(self) -> _Element:
        return super().load_xml()


class DOneTips(BaseModel, frozen=True):
    # TODO: require at least one tip position not be None
    position_1: Tip | None = None
    position_2: Tip | None = None

    @cached_property
    def first_available_position(self) -> Tip:
        if self.position_1 is not None:
            return self.position_1
        assert self.position_2 is not None, (
            "At least one tip position must be defined"
        )  # TODO: validate this in the model_post_init
        return self.position_2

    @cached_property
    def second_available_position(self) -> Tip | None:
        if self.position_1 is None:
            return None
        return self.position_2
