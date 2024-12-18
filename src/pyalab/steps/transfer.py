import json
from typing import Any
from typing import override

from pyalab.plate import Plate

from .base import Step
from .base import ul_to_xml


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
    """The volume to transfer."""

    @override
    def _add_value_groups(self) -> None:
        source_info: list[dict[str, Any]] = [
            {
                "Wells": [
                    {
                        "Item1": self.source_column_index,
                        "Item2": 0,  # TODO: handle row index
                    }
                ],
                "DeckSection": self.source_section_index,
                "SubSection": -1,  # TODO: figure out what subsection means
                "Spacing": 900,  # TODO: handle spacing other than 96-well plate
                "DeckId": "00000000-0000-0000-0000-000000000000",  # TODO: figure out if this has any meaning
                "WorkingDirectionExtended": 0,  # TODO: figure out what this is
                "WorkingDirectionOld": "false",  # TODO: figure out what this is
            }
        ]
        target_info: list[dict[str, Any]] = [
            {
                "Wells": [
                    {
                        "Item1": self.destination_column_index,
                        "Item2": 0,  # TODO: handle row index
                    }
                ],
                "DeckSection": self.destination_section_index,
                "SubSection": -1,  # TODO: figure out what subsection means
                "Spacing": 900,  # TODO: handle spacing other than 96-well plate
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
                            {
                                "DeckSection": self.source_section_index,
                                "SubSection": -1,
                                "OffsetX": 0,
                                "OffsetY": 0,
                            }
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
                            {
                                "DeckSection": self.destination_section_index,
                                "SubSection": -1,
                                "OffsetX": 0,
                                "OffsetY": 0,
                            }
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
                                "Well": {"Item1": self.destination_column_index, "Item2": 0},
                                "DeckSection": self.destination_section_index,
                                "SubSection": -1,
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
                                "Well": {"Item1": self.source_column_index, "Item2": 0},
                                "DeckSection": self.source_section_index,
                                "SubSection": -1,
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
                                "DeckSection": self.source_section_index,
                                "SubSection": -1,
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
                                "DeckSection": self.source_section_index,
                                "SubSection": -1,
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
                                "Well": {"Item1": self.destination_column_index, "Item2": 0},
                                "DeckSection": self.destination_section_index,
                                "SubSection": -1,
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
                                "DeckSection": self.destination_section_index,
                                "SubSection": -1,
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
                                "DeckSection": self.destination_section_index,
                                "SubSection": -1,
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
                                "Well": {"Item1": self.source_column_index, "Item2": 0},
                                "DeckSection": self.source_section_index,
                                "SubSection": -1,
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
                                "DeckSection": self.source_section_index,
                                "SubSection": -1,
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
                                "Well": {"Item1": self.source_column_index, "Item2": 0},
                                "DeckSection": self.source_section_index,
                                "SubSection": -1,
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
                                "Well": {"Item1": self.destination_column_index, "Item2": 0},
                                "DeckSection": self.destination_section_index,
                                "SubSection": -1,
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
                                "DeckSection": self.destination_section_index,
                                "SubSection": -1,
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
                                "Well": {"Item1": self.destination_column_index, "Item2": 0},
                                "DeckSection": self.destination_section_index,
                                "SubSection": -1,
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
                                "DeckSection": self.destination_section_index,
                                "SubSection": -1,
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
