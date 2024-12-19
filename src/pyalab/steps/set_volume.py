import json
from typing import Any
from typing import override

from pydantic import Field

from pyalab.plate import Plate

from .base import Section
from .base import Step
from .base import WellRowCol
from .base import ul_to_xml


class SetVolume(Step):
    """Specify the volume of liquid in the labware.

    Can be used to initially define it at the beginning of a protocol, or after a manual filling step.
    """

    type = "ManualFilling"
    plate: Plate
    """The plate to set the volume for."""
    section_index: int | None = None
    """The section of the Deck holding the plate."""
    column_index: int
    """The column within the plate to set the volume for."""
    volume: float = Field(ge=0)
    """The specified volume (µl)."""

    @override
    def _add_value_groups(self) -> None:
        assert self.section_index is not None, "section_index must be set prior to creating XML"
        well = WellRowCol(
            column_index=self.column_index,
            row_index=0,  # TODO: handle row index
        )
        deck_section = Section(
            section=self.section_index,
            sub_section=-1,  # TODO: figure out what subsection means
        )
        volume_info: list[dict[str, Any]] = [
            {
                "WellCoordinates": [
                    well.model_dump(by_alias=True),
                ],
                "Volume": ul_to_xml(self.volume),
                **deck_section.model_dump(by_alias=True),
                "Spacing": 900,  # TODO: handle spacing other than 96-well plate
                "ColorIndex": 1,  # TODO: figure out if/when this changes
                "DeckId": "00000000-0000-0000-0000-000000000000",  # TODO: figure out if this has any meaning
            }
        ]

        self._add_value_group(
            group_name="ManualVolume",
            values=[
                ("ManualVolume", json.dumps(volume_info)),
                ("MessageType", "null"),
                ("Message1", "null"),
                ("Message2", "null"),
                ("Message3", "null"),
                ("ShowMessageOnPipette", "false"),
            ],
        )


class SetInitialVolume(SetVolume):
    """Must be used as the first step in the program that set's the volume.

    Uses the same parameters as SetVolume.
    """

    type = "ManualFilling_First"
