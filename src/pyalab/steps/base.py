import json
import uuid
from abc import ABC
from abc import abstractmethod
from typing import ClassVar

from inflection import camelize
from lxml import etree
from lxml.etree import _Element
from pydantic import BaseModel
from pydantic import Field

from pyalab.pipette import Tip


def ul_to_xml(volume: float) -> int:
    # Vialab uses 0.01 uL as the base unit for volume, so convert from uL
    return int(round(volume * 100, 0))


def mm_to_xml(distance: float) -> int:
    # Vialab uses 0.01 mm as the base unit for distance, so convert from mm
    return int(round(distance * 100, 0))


SPECIAL_CHARS = ('"', "[", "]", "{", "}")

ALIASES = {"column_index": "Item1", "row_index": "Item2"}


def alias_generator(name: str) -> str:
    return ALIASES.get(name, name)


class WellRowCol(BaseModel, frozen=True):
    column_index: int = Field(ge=0)
    row_index: int = Field(ge=0)
    model_config = {
        "populate_by_name": True,  # Allow population by field name
        "alias_generator": alias_generator,
    }


class DeckSection(BaseModel, frozen=True):
    deck_section: int
    sub_section: int
    model_config = {
        "populate_by_name": True,  # Allow population by field name
        "alias_generator": camelize,  # Convert field names to camelCase
    }


class Section(BaseModel, frozen=True):
    """Some steps call it Section instead of DeckSection."""

    section: int
    sub_section: int
    model_config = {
        "populate_by_name": True,  # Allow population by field name
        "alias_generator": camelize,  # Convert field names to camelCase
    }


class WellOffsets(BaseModel, frozen=True):
    deck_section: int
    sub_section: int
    offset_x: int
    offset_y: int

    model_config = {
        "populate_by_name": True,  # Allow population by field name
        "alias_generator": camelize,  # Convert field names to camelCase
    }


class Step(BaseModel, ABC):
    type: ClassVar[str]
    _tip: Tip | None = None

    def set_tip(self, tip: Tip) -> None:
        self._tip = tip

    @property
    def tip(self) -> Tip:
        assert self._tip is not None
        return self._tip

    @property
    def tip_id(self) -> int:
        return self.tip.tip_id

    def create_xml_for_program(self) -> _Element:
        root = etree.Element("Step")
        for name, value in [
            ("Type", self.type),
            ("IsEnabled", "true"),
            ("ID", str(uuid.uuid4())),
            ("IsNew", json.dumps(obj=False)),
            (
                "DeckID",
                "00000000-0000-0000-0000-000000000000",
            ),  # TODO: figure out what this is and if it needs to be changed
        ]:
            etree.SubElement(root, name).text = value

        self._value_groups_node = etree.SubElement(root, "ValueGroups")
        self._add_value_groups()
        return root

    @abstractmethod
    def _add_value_groups(self) -> None: ...

    def _add_value_group(self, *, group_name: str, values: list[tuple[str, str]]) -> None:
        group_node = etree.SubElement(self._value_groups_node, "ValueGroup", attrib={"Key": group_name})
        values_node = etree.SubElement(group_node, "Values")
        for name, value in values:
            is_c_data_needed = any(char in value for char in SPECIAL_CHARS)
            etree.SubElement(values_node, "Value", attrib={"Key": name}).text = (
                etree.CDATA(value) if is_c_data_needed else value
            )
