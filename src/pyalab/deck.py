from enum import Enum

from pydantic import BaseModel


class StandardDeck(Enum):
    THREE_POSITION = "3 Position Universal Deck V12"
    FOUR_POSITION = "4 Position Portrait Deck V02"


class Deck(BaseModel):
    name: str | StandardDeck
