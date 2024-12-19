import json
from typing import Any
from typing import override

from pydantic import Field

from pyalab.plate import Plate

from .base import Step
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
        volume_info: list[dict[str, Any]] = [
            {
                "WellCoordinates": [
                    {
                        "Item1": self.column_index,
                        "Item2": 0,  # TODO: handle row index
                    }
                ],
                "Volume": ul_to_xml(self.volume),
                "Section": self.section_index,
                "SubSection": -1,  # TODO: figure out what subsection means
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
