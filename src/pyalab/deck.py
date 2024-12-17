from enum import Enum

from .integra_xml import LibraryComponent
from .integra_xml import LibraryComponentType


class StandardDeck(Enum):
    THREE_POSITION = "3 Position Universal Deck V12"
    FOUR_POSITION = "4 Position Portrait Deck V02"


class Deck(LibraryComponent):
    type = LibraryComponentType.DECK
    name: str
