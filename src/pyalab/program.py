from pathlib import Path

from pydantic import BaseModel

from .deck import Deck


class Program(BaseModel):
    deck: Deck

    def dump_xml(self, file_path: Path) -> None:
        pass
