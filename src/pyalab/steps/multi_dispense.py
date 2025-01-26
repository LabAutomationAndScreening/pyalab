import json
from typing import Any
from typing import override

from pydantic import Field

from .base import WORKING_DIRECTION_KWARGS
from .base import DeckSection
from .base import MixLocation
from .base import WellOffsets
from .base import WellRowCol
from .base import mm_to_xml
from .base import ul_to_xml
from .builders import LiquidTransferStep
from .params import AspirateParameters
from .params import DispenseParameters
from .params import PipettingLocation
from .params import TipChangeMode

type Volume = float


class MultiDispense(LiquidTransferStep):
    """Perform a multi/repeat dispense from a single source into one or more destinations."""

    # TODO: handle different explicit pipette span for source vs destinations

    type = "RepeatDispense"
    source: PipettingLocation
    """The source labware to aspirate from."""
    destinations: list[tuple[PipettingLocation, Volume]]
    """The destinations and volumes to dispense."""
    reverse_pipetting_volume: float = 0
    """The volume to aspirate prior to any volume planned to be dispensed."""
    pre_dispense_volume: float = 0
    """Extra volume to be dispensed back into the source prior to the main dispenses."""
    aspirate_parameters: AspirateParameters = Field(default_factory=AspirateParameters)
    """The parameters for aspirating the liquid."""
    dispense_parameters: DispenseParameters = Field(default_factory=DispenseParameters)
    """The parameters for dispensing the liquid."""
    # TODO: implement variable dispense heights for each dispense
    tip_change_mode: TipChangeMode = TipChangeMode.AFTER_STEP

    @override
    def _add_value_groups(self) -> None:
        # TODO: support multiple dispenses
        assert len(self.destinations) == 1, "Only single destination transfers are supported at this time."
        source_deck_section_model = DeckSection(
            deck_section=self.source.deck_section_index,
            sub_section=-1,  # TODO: figure out what subsection means
        )
        source_deck_section = source_deck_section_model.model_dump(by_alias=True)
        destination_deck_section_model = DeckSection(
            deck_section=self.destinations[0][0].deck_section_index, sub_section=-1
        )
        destination_deck_section = destination_deck_section_model.model_dump(by_alias=True)
        source_well = WellRowCol(column_index=self.source.column_index, row_index=0).model_dump(
            by_alias=True
        )  # TODO: handle row index
        destination_well = WellRowCol(column_index=self.destinations[0][0].column_index, row_index=0).model_dump(
            by_alias=True
        )  # TODO: handle row index
        source_info: list[dict[str, Any]] = [
            {
                "Wells": [source_well],
                **source_deck_section,
                "Spacing": mm_to_xml(self._pipette_span(self.source.labware)),
                **WORKING_DIRECTION_KWARGS,
            }
        ]
        target_info: list[dict[str, Any]] = [
            {
                "Wells": [destination_well],
                **destination_deck_section,
                "Spacing": mm_to_xml(self._pipette_span(self.destinations[0][0].labware)),
                **WORKING_DIRECTION_KWARGS,
            }
        ]

        self._add_value_group(
            group_name="Source",
            values=[
                ("MultiSelection", json.dumps(source_info)),
                (
                    "WellOffsets",
                    json.dumps(
                        [
                            WellOffsets(offset_x=0, offset_y=0, **source_deck_section_model.model_dump()).model_dump(
                                by_alias=True
                            )
                        ]
                    ),
                ),
            ],
        )
        self._add_value_group(
            group_name="Target",
            values=[
                ("MultiSelection", json.dumps(target_info)),
                (
                    "WellOffsets",
                    json.dumps(
                        [
                            WellOffsets(
                                offset_x=0, offset_y=0, **destination_deck_section_model.model_dump()
                            ).model_dump(by_alias=True)
                        ]
                    ),
                ),
            ],
        )
        self._add_value_group(
            group_name="Pipetting",
            values=[
                ("ExtraVolumePercentage", str(0)),
                ("NumberOfReactions", str(1)),  # TODO: handle multiple transfers in a single Step
                (
                    "DispenseVolume",
                    json.dumps(
                        [
                            {
                                "Well": destination_well,
                                **destination_deck_section,
                                "Volume": ul_to_xml(self.destinations[0][1]),
                                "TipID": self.tip_id,
                                "Multiplier": 1,
                                "TotalVolume": ul_to_xml(
                                    self.destinations[0][1]
                                ),  # TODO: figure out when/if this needs to differ from Volume
                            }
                        ]
                    ),
                ),
                (
                    "TipTypePipettingConfiguration",
                    json.dumps(
                        [
                            {
                                "FirstDispenseVolume": ul_to_xml(self.pre_dispense_volume),
                                "LastDispenseVolume": ul_to_xml(self.reverse_pipetting_volume),
                                "Airgap": False,
                                "AirgapVolume": 0,
                                "AspirationSpeed": self.aspirate_parameters.liquid_speed,
                                "DispenseSpeed": self.dispense_parameters.liquid_speed,
                                "TipID": self.tip_id,
                            }
                        ]
                    ),
                ),
                ("AspirationDelay", str(self.aspirate_parameters.post_delay)),
                ("DispenseDelay", str(self.dispense_parameters.post_delay)),
                ("KeepPostDispense", json.dumps(obj=True)),
                ("LastDispenseType", json.dumps(obj=True)),
                ("LastAspirationBackTo", '"Common_No"'),
                ("VolumeConfigType", json.dumps(obj=False)),  # TODO: figure out what this means
                ("DispenseType", json.dumps(obj=True)),  # TODO: figure out what this means
                ("SlowLiquidExitAsp", json.dumps(obj=False)),
                ("SlowLiquidExitDisp", json.dumps(obj=False)),
            ],
        )
        self._add_value_group(
            group_name="Aspiration",
            values=[
                (
                    "Heights",
                    json.dumps(
                        [
                            {
                                "Well": source_well,
                                **source_deck_section,
                                "StartHeight": mm_to_xml(self.aspirate_parameters.start_height),
                                "EndHeight": mm_to_xml(
                                    self.aspirate_parameters.start_height
                                ),  # TODO: implement moving aspirate
                                "TipID": self.tip_id,
                            }
                        ]
                    ),
                ),
                ("TipTravel", json.dumps(obj=False)),
                (
                    "SectionHeightConfig",
                    json.dumps(
                        [
                            {
                                **source_deck_section,
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
                                **source_deck_section,
                                "WellBottomOffset": 200,
                                "TipID": self.tip_id,
                            }
                        ]
                    ),
                ),
            ],
        )
        self._add_value_group(
            group_name="Dispense",
            values=[
                (
                    "Heights",
                    json.dumps(
                        [
                            {
                                "Well": destination_well,
                                **destination_deck_section,
                                "StartHeight": mm_to_xml(self.dispense_parameters.start_height),
                                "EndHeight": mm_to_xml(self.dispense_parameters.start_height),
                                "TipID": self.tip_id,
                            }
                        ]
                    ),
                ),
                ("TipTravel", json.dumps(obj=False)),
                (
                    "SectionHeightConfig",
                    json.dumps(
                        [
                            {
                                **destination_deck_section,
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
                                **destination_deck_section,
                                "WellBottomOffset": 200,
                                "TipID": self.tip_id,
                            }
                        ]
                    ),
                ),
            ],
        )
        self._add_tips_value_group()
        self._add_mix_group(
            mix_location=MixLocation.SOURCE, well_info=source_well, deck_section_info=source_deck_section
        )
        self._add_mix_group(
            mix_location=MixLocation.DESTINATION, well_info=destination_well, deck_section_info=destination_deck_section
        )

        self._add_tip_touch_target_group(destination_deck_section)

        self._add_various_value_group()

        self._add_lld_value_group()
