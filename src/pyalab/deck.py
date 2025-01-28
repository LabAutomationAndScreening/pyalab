from enum import Enum
from typing import ClassVar
from typing import Literal

from lxml import etree
from lxml.etree import _Element
from pydantic import BaseModel

from .integra_xml import LibraryComponent
from .integra_xml import LibraryComponentType
from .integra_xml import hundredths_mm_to_mm
from .plate import Labware


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


class LabwareOrientation(Enum):
    # TODO: handle inverted orientations (e.g. A1 in bottom right or bottom left)
    A1_NW_CORNER = "Landscape"
    A1_NE_CORNER = "Portrait_Inverse"
    A1_SW_CORNER = "Portrait"  # TODO: test pipetting in this orientation


class DeckPosition(BaseModel, frozen=True):
    name: Literal["A", "B", "C", "D"]
    orientation: LabwareOrientation
    _section_match_epsilon: ClassVar[float] = 4
    # Allow the section width and length to be +/- some amount from the labware footprint when searching for a compatible section (sometimes the footprint is larger, like INTEGRA 10 ml Multichannel Reservoir in Slot A)
    # The Rack for 1.5 ml microcentrifuge tubes Tubeholder is nearly 4 mm different than the deck section

    def section_index(self, *, deck: Deck, labware: Labware) -> int:
        root = deck.load_xml()
        is_portrait = self.orientation in (LabwareOrientation.A1_NE_CORNER, LabwareOrientation.A1_SW_CORNER)
        labware_search_width = labware.length if is_portrait else labware.width
        labware_search_length = labware.width if is_portrait else labware.length
        for idx, section in enumerate(root.findall("./Sections/Section")):
            name = section.find("Name")
            width = section.find("Width")
            length = section.find("Length")
            assert width is not None
            assert width.text is not None
            assert length is not None
            assert length.text is not None
            assert name is not None

            if (
                name.text == self.name
                and abs(hundredths_mm_to_mm(width.text) - labware_search_width) <= self._section_match_epsilon
                and abs(hundredths_mm_to_mm(length.text) - labware_search_length) <= self._section_match_epsilon
            ):
                return idx  # TODO: confirm that Integra does not allow any duplicates inherently

        raise DeckPositionNotFoundError(
            deck_name=deck.name, deck_position_name=self.name, width=labware.xml_width, length=labware.xml_length
        )
        # TODO: figure out if CreationOrderIndex is important to be changed or not


class DeckLayout(BaseModel):
    deck: Deck
    labware: dict[DeckPosition, Labware]
    name: str = ""

    def create_xml_for_program(self, *, layout_num: int) -> _Element:
        name = self.name if self.name != "" else f"Labware Layout {layout_num}"

        root = self.deck.create_xml_for_program()
        _ = etree.SubElement(root, "NameInProcess").text = name
        for deck_position, plate in self.labware.items():
            section_idx = deck_position.section_index(deck=self.deck, labware=plate)

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
                    for child in list(section):
                        if child.tag == "OrientationExtended":
                            child.text = deck_position.orientation.value
                            break
                    else:
                        raise NotImplementedError(
                            "Could not find <OrientationExtended> element in the section...this should never happen so there's no implementation to handle it"
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
