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
        root = self.load_xml()
        tip_id_node = root.find(".//TipID")
        assert tip_id_node is not None
        tip_id_text = tip_id_node.text
        assert tip_id_text is not None
        return int(tip_id_text)
