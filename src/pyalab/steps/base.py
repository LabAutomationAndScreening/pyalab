import json
import uuid
from abc import ABC
from abc import abstractmethod
from enum import Enum
from typing import Any
from typing import ClassVar

from inflection import camelize
from lxml import etree
from lxml.etree import _Element
from pydantic import BaseModel
from pydantic import Field

from pyalab.pipette import Pipette
from pyalab.pipette import Tip

WORKING_DIRECTION_KWARGS: dict[str, Any] = {
    "DeckId": "00000000-0000-0000-0000-000000000000",  # TODO: figure out if this has any meaning
    "WorkingDirectionExtended": 0,  # TODO: figure out what this is
    "WorkingDirectionOld": "false",  # TODO: figure out what this is
}


class MixLocation(Enum):
    SOURCE = "SourceMix"
    DESTINATION = "TargetMix"


class Location(Enum):
    SOURCE = "Source"
    DESTINATION = "Target"


class LldErrorHandlingMode(Enum):
    PAUSE_AND_REPEAT = "LLD_PauseAndRepeat"


def ul_to_xml(volume: float) -> int:
    # Vialab uses 0.01 uL as the base unit for volume, so convert from uL
    return int(round(volume * 100, 0))


def mm_to_xml(distance: float) -> int:
    # Vialab uses 0.01 mm as the base unit for distance, so convert from mm
    return int(round(distance * 100, 0))


SPECIAL_CHARS = ('"', "[", "]", "{", "}")

ALIASES = {"column_index": "Item1", "row_index": "Item2"}


def alias_generator(name: str) -> str:
    return ALIASES.get(name, name)


class WellRowCol(BaseModel, frozen=True):
    column_index: int = Field(ge=0)
    row_index: int = Field(ge=0)
    model_config = {
        "populate_by_name": True,  # Allow population by field name
        "alias_generator": alias_generator,
    }


class DeckSection(BaseModel, frozen=True):
    deck_section: int
    sub_section: int
    model_config = {
        "populate_by_name": True,  # Allow population by field name
        "alias_generator": camelize,  # Convert field names to camelCase
    }


class Section(BaseModel, frozen=True):
    """Some steps call it Section instead of DeckSection."""

    section: int
    sub_section: int
    model_config = {
        "populate_by_name": True,  # Allow population by field name
        "alias_generator": camelize,  # Convert field names to camelCase
    }


class WellOffsets(BaseModel, frozen=True):
    deck_section: int
    sub_section: int
    offset_x: int
    offset_y: int

    model_config = {
        "populate_by_name": True,  # Allow population by field name
        "alias_generator": camelize,  # Convert field names to camelCase
    }


class LiquidMovementParameters(BaseModel, frozen=True):
    start_height: float = 3.3
    """The height to start aspirating or dispensing from (mm)."""
    end_height: float | None = None  # TODO: implement moving aspiration/dispense
    """The height to stop at in mm, (None for fixed height)."""
    liquid_speed: int = 8
    """The speed the liquid should move at (Integra Numbers, 1-10)."""
    # TODO: use uL/sec instead of the Integra numbers here, and then convert within the XML generation
    post_delay: int = 0  # it seems like ViaLab only supports integer seconds delay..at least in the UI
    """The number of seconds to delay after the liquid movement is finished."""


class Step(BaseModel, ABC):
    type: ClassVar[str]
    _tip: Tip | None = None
    _pipette: Pipette | None = None

    def set_pipette(self, pipette: Pipette) -> None:
        self._pipette = pipette

    @property
    def pipette(self) -> Pipette:
        assert self._pipette is not None
        return self._pipette

    def set_tip(self, tip: Tip) -> None:
        self._tip = tip

    @property
    def tip(self) -> Tip:
        assert self._tip is not None
        return self._tip

    @property
    def tip_id(self) -> int:
        return self.tip.tip_id

    def create_xml_for_program(self) -> _Element:
        root = etree.Element("Step")
        for name, value in [
            ("Type", self.type),
            ("IsEnabled", "true"),
            ("ID", str(uuid.uuid4())),
            ("IsNew", json.dumps(obj=False)),
            (
                "DeckID",
                "00000000-0000-0000-0000-000000000000",
            ),  # TODO: figure out what this is and if it needs to be changed
        ]:
            etree.SubElement(root, name).text = value

        self._value_groups_node = etree.SubElement(root, "ValueGroups")
        self._add_value_groups()
        return root

    @abstractmethod
    def _add_value_groups(self) -> None: ...

    def _add_value_group(self, *, group_name: str, values: list[tuple[str, str]]) -> None:
        group_node = etree.SubElement(self._value_groups_node, "ValueGroup", attrib={"Key": group_name})
        values_node = etree.SubElement(group_node, "Values")
        for name, value in values:
            is_c_data_needed = any(char in value for char in SPECIAL_CHARS)
            etree.SubElement(values_node, "Value", attrib={"Key": name}).text = (
                etree.CDATA(value) if is_c_data_needed else value
            )

    def _add_lld_value_group(self) -> None:
        self._add_value_group(
            group_name="LLD",
            values=[
                ("UseLLD", json.dumps(obj=False)),
                ("LLDErrorHandling", json.dumps(LldErrorHandlingMode.PAUSE_AND_REPEAT.value)),
                ("LLDHeights", json.dumps(None)),
            ],
        )

    def _add_various_value_group(self) -> None:
        self._add_value_group(
            group_name="Various",
            values=[
                ("SpeedX", str(10)),
                ("SpeedY", str(10)),
                ("SpeedZ", str(10)),
                ("IsStepActive", json.dumps(obj=True)),
            ],
        )

    def _add_mix_group(
        self, *, mix_location: MixLocation, well_info: dict[str, Any], deck_section_info: dict[str, Any]
    ):
        values = [
            ("MixActive", json.dumps(obj=False)),
            (
                "TipTypeMixConfiguration",
                json.dumps(
                    obj=[
                        {
                            "MixSpeed": 8,
                            "TipID": self.tip_id,
                        }
                    ]
                ),
            ),
            ("MixPause", json.dumps(obj=0)),
            (
                "SectionMixVolume",
                json.dumps(
                    obj=[
                        {
                            "Well": well_info,
                            **deck_section_info,
                            "Volume": 5000,  # TODO: implement mixing volume
                            "TipID": self.tip_id,
                            "Multiplier": 1,
                            "TotalVolume": 5000,  # TODO: figure out when/if this needs to differ from Volume
                        }
                    ]
                ),
            ),
            ("MixCycles", json.dumps(obj=3)),
            ("BlowOut", json.dumps(obj=False)),
            ("TipTravel", json.dumps(obj=False)),
            (
                "SectionHeightConfig",
                json.dumps(
                    obj=[
                        {
                            **deck_section_info,
                            "HeightConfigType": True,
                            "WellBottomOffset": 0,
                        }
                    ]
                ),
            ),
            ("VolumeConfigType", json.dumps(obj=True)),
            (
                "Heights",
                json.dumps(
                    obj=[
                        {
                            "Well": well_info,
                            **deck_section_info,
                            "StartHeight": 325,
                            "EndHeight": 0,
                            "TipID": self.tip_id,
                        }
                    ]
                ),
            ),
            ("MixBeforeEachAspiration", json.dumps(obj=False)),
        ]
        if mix_location == MixLocation.DESTINATION:
            values.append(("SkipFirst", json.dumps(obj=False)))
        self._add_value_group(
            group_name=mix_location.value,
            values=values,
        )

    def _create_height_config_value_tuples(self, *, deck_section_info: dict[str, Any]) -> list[tuple[str, str]]:
        return [
            (
                "SectionHeightConfig",
                json.dumps(
                    [
                        {
                            **deck_section_info,
                            "HeightConfigType": True,
                            "WellBottomOffset": 0,
                        }
                    ]
                ),
            ),
            (
                "TipTypeHeightConfiguration",
                json.dumps(
                    [
                        {
                            **deck_section_info,
                            "WellBottomOffset": 200,
                            "TipID": self.tip_id,
                        }
                    ]
                ),
            ),
        ]

    def _create_heights_value_tuple(
        self, *, well_info: dict[str, Any], deck_section_info: dict[str, Any], start_height: float
    ) -> tuple[str, str]:
        end_height = start_height  # TODO: implement moving aspirate/dispense
        return (
            "Heights",
            json.dumps(
                [
                    {
                        "Well": well_info,
                        **deck_section_info,
                        "StartHeight": mm_to_xml(start_height),
                        "EndHeight": mm_to_xml(end_height),
                        "TipID": self.tip_id,
                    }
                ]
            ),
        )

    def _add_location_group(self, *, location: Location, well_info: list[dict[str, Any]], deck_section: DeckSection):
        values = [
            ("MultiSelection", json.dumps(well_info)),
            (
                "WellOffsets",
                json.dumps(
                    [WellOffsets(offset_x=0, offset_y=0, **deck_section.model_dump()).model_dump(by_alias=True)]
                ),
            ),
        ]
        self._add_value_group(group_name=location.value, values=values)
