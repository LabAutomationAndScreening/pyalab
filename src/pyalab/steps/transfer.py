import json
from typing import Any
from typing import override

from pydantic import Field

from pyalab.plate import Plate

from .base import DeckSection
from .base import LldErrorHandlingMode
from .base import Step
from .base import WellOffsets
from .base import WellRowCol
from .base import mm_to_xml
from .base import ul_to_xml
from .params import AspirateParameters


class Transfer(Step):
    """Simple transfer from one column to another."""

    type = "Transfer"
    source: Plate
    """The source plate to aspirate from."""
    destination: Plate
    """The destination plate to dispense into."""
    source_section_index: int | None = None
    """The section index on the Deck of the source plate."""
    source_column_index: int
    """The column index to aspirate from."""
    destination_section_index: int | None = None
    """The section index on the Deck of the destination plate."""
    destination_column_index: int
    """The column index to dispense into."""
    volume: float
    """The volume to transfer (µl)."""
    aspirate_parameters: AspirateParameters = Field(default_factory=AspirateParameters)
    """The parameters for aspirating the liquid."""

    @override
    def _add_value_groups(self) -> None:
        assert self.source_section_index is not None, "Source section index must be set prior to creating XML"
        assert self.destination_section_index is not None, "Destination section index must be set prior to creating XML"
        source_deck_section_model = DeckSection(
            deck_section=self.source_section_index,
            sub_section=-1,  # TODO: figure out what subsection means
        )
        source_deck_section = source_deck_section_model.model_dump(by_alias=True)
        destination_deck_section_model = DeckSection(deck_section=self.destination_section_index, sub_section=-1)
        destination_deck_section = destination_deck_section_model.model_dump(by_alias=True)
        source_well = WellRowCol(column_index=self.source_column_index, row_index=0).model_dump(
            by_alias=True
        )  # TODO: handle row index
        destination_well = WellRowCol(column_index=self.destination_column_index, row_index=0).model_dump(
            by_alias=True
        )  # TODO: handle row index
        source_info: list[dict[str, Any]] = [
            {
                "Wells": [source_well],
                **source_deck_section,
                "Spacing": mm_to_xml(
                    self.source.row_spacing
                ),  # TODO: handle spacing based on landscape vs portrait orientation
                "DeckId": "00000000-0000-0000-0000-000000000000",  # TODO: figure out if this has any meaning
                "WorkingDirectionExtended": 0,  # TODO: figure out what this is
                "WorkingDirectionOld": "false",  # TODO: figure out what this is
            }
        ]
        target_info: list[dict[str, Any]] = [
            {
                "Wells": [destination_well],
                **destination_deck_section,
                "Spacing": mm_to_xml(
                    self.destination.row_spacing
                ),  # TODO: handle spacing based on landscape vs portrait orientation
                "DeckId": "00000000-0000-0000-0000-000000000000",  # TODO: figure out if this has any meaning
                "WorkingDirectionExtended": 0,  # TODO: figure out what this is
                "WorkingDirectionOld": "false",  # TODO: figure out what this is
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
                                "Volume": ul_to_xml(self.volume),
                                "TipID": self.tip_id,
                                "Multiplier": 1,
                                "TotalVolume": ul_to_xml(
                                    self.volume
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
                                "FirstDispenseVolume": 0,
                                "LastDispenseVolume": 0,
                                "Airgap": False,
                                "AirgapVolume": 0,
                                "AspirationSpeed": 8,
                                "DispenseSpeed": 8,
                                "TipID": self.tip_id,
                            }
                        ]
                    ),
                ),
                ("AspirationDelay", str(0)),
                ("DispenseDelay", str(0)),
                ("KeepPostDispense", json.dumps(obj=False)),
                ("LastDispenseType", json.dumps(obj=True)),
                ("LastAspirationBackTo", '"Common_No"'),
                ("VolumeConfigType", json.dumps(obj=True)),
                ("DispenseType", json.dumps(obj=False)),
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
                                "EndHeight": 325,  # TODO: implement moving aspirate
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
                                "StartHeight": 325,  # TODO: figure out how these height values are determined
                                "EndHeight": 325,
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
        self._add_value_group(
            group_name="Tips",
            values=[
                ("PreWetting", json.dumps(obj=False)),
                ("PreWettingCycles", json.dumps(obj=3)),
                ("TipChange", '"TipChange_ModeA"'),
                ("TipEjectionType", json.dumps(obj=True)),
            ],
        )
        self._add_value_group(
            group_name="SourceMix",
            values=[
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
                                "Well": source_well,
                                **source_deck_section,
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
                                **source_deck_section,
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
                                "Well": source_well,
                                **source_deck_section,
                                "StartHeight": 325,  # TODO: figure out how these height values are determined
                                "EndHeight": 0,
                                "TipID": self.tip_id,
                            }
                        ]
                    ),
                ),
                ("MixBeforeEachAspiration", json.dumps(obj=False)),
            ],
        )
        self._add_value_group(
            group_name="TargetMix",
            values=[
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
                                "Well": destination_well,
                                **destination_deck_section,
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
                                **destination_deck_section,
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
                                "Well": destination_well,
                                **destination_deck_section,
                                "StartHeight": 325,  # TODO: figure out how these height values are determined
                                "EndHeight": 0,
                                "TipID": self.tip_id,
                            }
                        ]
                    ),
                ),
                ("MixBeforeEachAspiration", json.dumps(obj=False)),
                ("SkipFirst", json.dumps(obj=False)),
            ],
        )
        self._add_value_group(
            group_name="TipTouchTarget",
            values=[
                ("TipTouchActive", json.dumps(obj=False)),
                (
                    "SectionTipTouch",
                    json.dumps(
                        obj=[
                            {
                                **destination_deck_section,
                                "Type": False,
                                "Height": 1406,  # TODO: implement tip touch
                                "Distance": 225,
                            }
                        ]
                    ),
                ),
            ],
        )
        self._add_value_group(
            group_name="Various",
            values=[
                ("SpeedX", str(10)),
                ("SpeedY", str(10)),
                ("SpeedZ", str(10)),
                ("IsStepActive", json.dumps(obj=True)),
            ],
        )

        self._add_value_group(
            group_name="LLD",
            values=[
                ("UseLLD", json.dumps(obj=False)),
                ("LLDErrorHandling", json.dumps(LldErrorHandlingMode.PAUSE_AND_REPEAT.value)),
                ("LLDHeights", json.dumps(None)),
            ],
        )
