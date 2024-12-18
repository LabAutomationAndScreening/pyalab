from enum import Enum
from functools import cached_property
from typing import ClassVar
from typing import Literal

from lxml import etree
from lxml.etree import _Element
from pydantic import BaseModel

from .integra_xml import LibraryComponent
from .integra_xml import LibraryComponentType
from .plate import Plate


class StandardDeckNames(Enum):
    THREE_POSITION = "3 Position Universal Deck"
    FOUR_POSITION = "4 Position Portrait Deck"


class Deck(LibraryComponent, frozen=True):
    type: ClassVar[LibraryComponentType] = LibraryComponentType.DECK


class DeckPositionNotFoundError(Exception):
    def __init__(self, *, deck_name: str, deck_position_name: str, width: int, length: int):
        super().__init__(
            f"Could not find a position in the Deck {deck_name} with name {deck_position_name} of width {width} and length {length}"
        )


class DeckPosition(BaseModel, frozen=True):
    name: Literal["A", "B", "C", "D"]
    width: float
    length: float

    # the XML encodes the dimension in units of 0.01 mm, but our standard units are in mm
    @cached_property
    def xml_width(self) -> int:
        return int(round(self.width * 100, 0))

    @cached_property
    def xml_length(self) -> int:
        return int(round(self.length * 100, 0))

    def section_index(self, deck: Deck) -> int:
        root = deck.load_xml()
        for idx, section in enumerate(root.findall("./Sections/Section")):
            name = section.find("Name")
            width = section.find("Width")
            length = section.find("Length")
            assert width is not None
            assert length is not None
            assert name is not None

            if name.text == self.name and width.text == str(self.xml_width) and length.text == str(self.xml_length):
                return idx  # TODO: confirm that Integra does not allow any duplicates inherently

        raise DeckPositionNotFoundError(
            deck_name=deck.name, deck_position_name=self.name, width=self.xml_width, length=self.xml_length
        )
        # TODO: figure out if CreationOrderIndex is important to be changed or not


class DeckPositions(Enum):
    B_PLATE_LANDSCAPE = DeckPosition(name="B", length=128.2, width=86)
    C_PLATE_LANDSCAPE = DeckPosition(name="C", length=128.2, width=86)


class DeckLayout(BaseModel):
    deck: Deck
    labware: dict[DeckPosition, Plate]
    name: str = ""

    def create_xml_for_program(self, *, layout_num: int) -> _Element:
        name = self.name if self.name != "" else f"Labware Layout {layout_num}"

        root = self.deck.create_xml_for_program()
        _ = etree.SubElement(root, "NameInProcess").text = name
        for deck_position, plate in self.labware.items():
            section_idx = deck_position.section_index(self.deck)

            for idx, section in enumerate(root.findall("./Sections/Section")):
                if idx == section_idx:
                    plate_xml = plate.create_xml_for_program()
                    children = list(section)
                    for index, child in enumerate(list(section)):
                        if child.tag == "IsWaste":
                            # Insert the new element right after <IsWaste>
                            children.insert(index + 1, plate_xml)
                            break
                    else:
                        raise NotImplementedError(
                            "Could not find <IsWaste> element in the section...this should never happen so there's no implementation to handle it"
                        )
                    # Clear existing children and re-insert the updated list
                    section.clear()
                    section.extend(children)

                    break
            else:
                raise NotImplementedError(
                    f"Could not find section with index {section_idx} in the deck XML...this should never happen so there's no implementation to handle it"
                )

        return root
