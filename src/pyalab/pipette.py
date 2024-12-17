from .integra_xml import LibraryComponent
from .integra_xml import LibraryComponentType


class Pipette(LibraryComponent):
    type = LibraryComponentType.PIPETTE
    name: str


class Tip(LibraryComponent):
    type = LibraryComponentType.TIP
    name: str
