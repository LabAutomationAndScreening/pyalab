import json
from typing import Any
from typing import override

from pydantic import Field

from pyalab.plate import Plate

from .base import WORKING_DIRECTION_KWARGS
from .base import DeckSection
from .base import Location
from .base import MixLocation
from .base import WellRowCol
from .base import mm_to_xml
from .base import ul_to_xml
from .builders import LiquidTransferStep
from .params import AspirateParameters
from .params import DispenseParameters
from .params import TipChangeMode


class Transfer(LiquidTransferStep):
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
    source_row_index: int = 0  # don't change from zero unless using a D-One pipette
    """The row index to aspirate from."""
    destination_section_index: int | None = None
    """The section index on the Deck of the destination plate."""
    destination_column_index: int
    """The column index to dispense into."""
    destination_row_index: int = 0  # don't change from zero unless using a D-One pipette
    """The row index to dispense into."""
    volume: float
    """The volume to transfer (µl)."""
    aspirate_parameters: AspirateParameters = Field(default_factory=AspirateParameters)
    """The parameters for aspirating the liquid."""
    dispense_parameters: DispenseParameters = Field(default_factory=DispenseParameters)
    """The parameters for dispensing the liquid."""

    tip_change_mode: TipChangeMode = TipChangeMode.MODE_A  # for now this is basically a class attribute that shouldn't be altered, but pyright complained about that. it's possible it actually is something that can be varied in a Transfer Step...TBD

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
        source_well = WellRowCol(column_index=self.source_column_index, row_index=self.source_row_index).model_dump(
            by_alias=True
        )
        destination_well = WellRowCol(
            column_index=self.destination_column_index, row_index=self.destination_row_index
        ).model_dump(by_alias=True)
        source_info: list[dict[str, Any]] = [
            {
                "Wells": [source_well],
                **source_deck_section,
                "Spacing": mm_to_xml(
                    self.source.row_spacing()
                ),  # TODO: handle spacing based on landscape vs portrait orientation
                **WORKING_DIRECTION_KWARGS,
            }
        ]
        target_info: list[dict[str, Any]] = [
            {
                "Wells": [destination_well],
                **destination_deck_section,
                "Spacing": mm_to_xml(
                    self.destination.row_spacing()
                ),  # TODO: handle spacing based on landscape vs portrait orientation
                **WORKING_DIRECTION_KWARGS,
            }
        ]
        # pylint:disable=duplicate-code # This seems decently DRY...there's just a bit of similarity between steps...which might disappear as more values are parametrized
        self._add_location_group(
            location=Location.SOURCE, well_info=source_info, deck_section=source_deck_section_model
        )
        self._add_location_group(
            location=Location.DESTINATION, well_info=target_info, deck_section=destination_deck_section_model
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
                                # pylint:enable=duplicate-code
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
                # pylint:disable=duplicate-code # This seems decently DRY...there's just a bit of similarity between steps...which might disappear as more values are parametrized
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
                self._create_heights_value_tuple(
                    well_info=source_well,
                    deck_section_info=source_deck_section,
                    start_height=self.aspirate_parameters.start_height,
                ),
                ("TipTravel", json.dumps(obj=False)),
                *self._create_height_config_value_tuples(
                    deck_section_info=source_deck_section,
                ),
            ],
        )
        self._add_value_group(
            group_name="Dispense",
            values=[
                self._create_heights_value_tuple(
                    well_info=destination_well,
                    deck_section_info=destination_deck_section,
                    start_height=self.dispense_parameters.start_height,
                ),
                ("TipTravel", json.dumps(obj=False)),
                *self._create_height_config_value_tuples(
                    deck_section_info=destination_deck_section,
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
        # pylint:enable=duplicate-code
