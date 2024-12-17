from enum import Enum

from pydantic import BaseModel


class LibraryComponentType(Enum):
    DECK = "deck"


class LibraryComponent(BaseModel):
    type: LibraryComponentType
    name: str
