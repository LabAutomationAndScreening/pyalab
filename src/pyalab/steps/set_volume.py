import json
from typing import Any
from typing import override

from pydantic import Field

from pyalab.plate import Labware

from .base import Section
from .base import WellRowCol
from .base import mm_to_xml
from .base import ul_to_xml
from .builders import StepWithPipetteSpan


# TODO: add ability during program generation to collapse consecutive SetVolume steps into a single step.  If there are descriptions, then maybe stop the collapse and create a new step so distinct descriptions are preserved
class SetVolume(StepWithPipetteSpan):
    """Specify the volume of liquid in the labware.

    Can be used to initially define it at the beginning of a protocol, or after a manual filling step.
    """

    type = "ManualFilling"
    labware: Labware
    """The plate to set the volume for."""
    section_index: int | None = None
    """The section of the Deck holding the plate."""
    column_index: int
    """The column within the plate to set the volume for."""
    row_index: int | None = None
    """The row index within the plate to set the volume for.

    This should only be used with the D-One pipette. Otherwise the entire column will just be set to the same volume.
    """
    volume: float = Field(ge=0)
    """The specified volume (µl)."""

    @override
    def _add_value_groups(self) -> None:
        assert self.section_index is not None, "section_index must be set prior to creating XML"
        well = WellRowCol(
            column_index=self.column_index,
            row_index=0 if self.row_index is None else self.row_index,
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
                "Spacing": mm_to_xml(
                    self.labware.row_spacing_in_xml if self.pipette.is_d_one else self._pipette_span(self.labware)
                ),
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
