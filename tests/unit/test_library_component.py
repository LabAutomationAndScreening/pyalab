import pytest

from pyalab import Deck
from pyalab import IntegraLibraryObjectNotFoundError
from pyalab import Plate


class TestLoadXmlFromStandardLibrary:
    @pytest.mark.parametrize(
        ("component_class", "component_name"),
        [
            pytest.param(Deck, "3 Position Universal Deck", id="a deck"),
            pytest.param(Plate, "BIO-RAD Hard-Shell 96-Well Skirted PCR Plates", id="a plate"),
        ],
    )
    def test_Given_no_version_specified_and_file_exists__Then_success(self, component_class: type, component_name: str):
        component = component_class(name=component_name)

        component.load_xml()

    @pytest.mark.parametrize(
        ("component_class", "component_name"),
        [
            pytest.param(Plate, "3 Position Universal Deck", id="looking for a deck in the plate folder"),
            pytest.param(
                Deck,
                "BIO-RAD Hard-Shell 96-Well Skirted PCR Plates1",
                id="looking for a plate in the deck folder",
            ),
        ],
    )
    def test_Given_file_does_not_exist__Then_error(self, component_class: type, component_name: str):
        component = component_class(name=component_name)

        with pytest.raises(
            IntegraLibraryObjectNotFoundError, match=rf"{component.type.value}.*{component_name}.*integra_library"
        ):
            component.load_xml()
