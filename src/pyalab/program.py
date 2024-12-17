from pydantic import BaseModel

from .deck import Deck


class Program(BaseModel):
    deck: Deck
