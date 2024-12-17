from .integra_xml import LibraryComponent
from .integra_xml import LibraryComponentType


class Plate(LibraryComponent):
    type = LibraryComponentType.PLATE
    name: str
