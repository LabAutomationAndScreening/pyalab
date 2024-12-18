import json
import uuid
from abc import ABC
from abc import abstractmethod
from typing import ClassVar

from lxml import etree
from lxml.etree import _Element
from pydantic import BaseModel

from pyalab.pipette import Tip


def ul_to_xml(volume: float) -> int:
    # ViaLab uses 0.01 uL as the base unit for volume, so convert from uL
    return int(round(volume * 100, 0))


SPECIAL_CHARS = ('"', "[", "]", "{", "}")


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
