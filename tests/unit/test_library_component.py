import pytest

from pyalab import IntegraLibraryObjectNotFoundError
from pyalab import LibraryComponent
from pyalab import LibraryComponentType


class TestLoadXmlFromStandardLibrary:
    @pytest.mark.parametrize(
        ("component_type", "component_name"),
        [
            pytest.param(LibraryComponentType.DECK, "3 Position Universal Deck", id="a deck"),
            pytest.param(LibraryComponentType.PLATE, "BIO-RAD Hard-Shell 96-Well Skirted PCR Plates", id="a plate"),
        ],
    )
    def test_Given_no_version_specified_and_file_exists__Then_success(
        self, component_type: LibraryComponentType, component_name: str
    ):
        component = LibraryComponent(type=component_type, name=component_name)

        component.load_xml()

    @pytest.mark.parametrize(
        ("component_type", "component_name"),
        [
            pytest.param(
                LibraryComponentType.PLATE, "3 Position Universal Deck", id="looking for a deck in the plate folder"
            ),
            pytest.param(
                LibraryComponentType.DECK,
                "BIO-RAD Hard-Shell 96-Well Skirted PCR Plates1",
                id="looking for a plate in the deck folder",
            ),
        ],
    )
    def test_Given_file_does_not_exist__Then_error(self, component_type: LibraryComponentType, component_name: str):
        component = LibraryComponent(type=component_type, name=component_name)

        with pytest.raises(
            IntegraLibraryObjectNotFoundError, match=rf"{component_type.value}.*{component_name}.*integra_library"
        ):
            component.load_xml()
