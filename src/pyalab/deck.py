from enum import Enum
from typing import ClassVar
from typing import Literal

from pydantic import BaseModel

from .integra_xml import LibraryComponent
from .integra_xml import LibraryComponentType
from .plate import Plate


class StandardDeckNames(Enum):
    THREE_POSITION = "3 Position Universal Deck"
    FOUR_POSITION = "4 Position Portrait Deck"


class Deck(LibraryComponent):
    type: ClassVar[LibraryComponentType] = LibraryComponentType.DECK


class DeckPosition(BaseModel, frozen=True):
    name: Literal["A", "B", "C", "D"]
    width: float
    length: float


class DeckPositions(Enum):
    B_PLATE_LANDSCAPE = DeckPosition(name="B", width=128.2, length=86)


class DeckLayout(BaseModel):
    deck: Deck
    labware: set[tuple[DeckPosition, Plate]]
