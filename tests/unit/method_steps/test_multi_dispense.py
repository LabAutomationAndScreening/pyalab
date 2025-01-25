import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import pytest

from pyalab import AspirateParameters
from pyalab import Deck
from pyalab import DeckLayout
from pyalab import DeckPosition
from pyalab import DispenseParameters
from pyalab import LabwareOrientation
from pyalab import MultiDispense
from pyalab import Pipette
from pyalab import PipettingLocation
from pyalab import Program
from pyalab import SetInitialVolume
from pyalab import StandardDeckNames
from pyalab import Tip
from pyalab import TipChangeMode

from ..constants import GENERIC_96_DEEP_WELL_PLATE
from ..fixtures import ProgramSnapshot


class TestMultiDispenseProgramSnapshots(ProgramSnapshot):
    @pytest.mark.parametrize(
        (
            "source_column_index",
            "destination_column_indexes_and_volumes",
            "aspirate_params",
            "dispense_params",
            "tip_change_mode",
            "reverse_pipetting_volume",
            "pre_dispense_volume",
        ),
        [
            pytest.param(
                3,
                [(8, 100)],
                None,
                None,
                None,
                None,
                None,
                id="test-default-params",
            ),
            pytest.param(
                4,
                [(3, 78.5)],
                AspirateParameters(liquid_speed=5, post_delay=2),
                DispenseParameters(liquid_speed=9, post_delay=1),
                TipChangeMode.NO_CHANGE,
                25,
                35,
                id="arbitrary1",
            ),
        ],
    )
    def test_arbitrary_params(  # noqa: PLR0913 # this is a lot of arguments to parametrize, but it makes it more efficient to not generate a bunch of separate snapshot files
        self,
        source_column_index: int,
        destination_column_indexes_and_volumes: list[tuple[int, float]],
        # use None to test not providing that kwarg to test the default value behavior
        aspirate_params: AspirateParameters | None,
        dispense_params: DispenseParameters | None,
        tip_change_mode: TipChangeMode | None,
        reverse_pipetting_volume: float | None,
        pre_dispense_volume: float | None,
    ):
        plate = GENERIC_96_DEEP_WELL_PLATE
        program = Program(
            deck_layouts=[
                DeckLayout(
                    deck=Deck(name=StandardDeckNames.THREE_POSITION.value),
                    labware={DeckPosition(name="B", orientation=LabwareOrientation.A1_NW_CORNER): plate},
                )
            ],
            display_name="arbitrary",
            description="arbitrary description",
            pipette=Pipette(name="VOYAGER EIGHT 300 µl"),
            tip=Tip(name="300 µl GripTip Sterile Filter Low retention"),
        )
        plate_section_index = program.get_section_index_for_plate(plate)

        program.add_step(
            SetInitialVolume(
                plate=plate,
                section_index=plate_section_index,
                column_index=source_column_index,
                volume=2000,
            )
        )
        for destination_column_index, _ in destination_column_indexes_and_volumes:
            program.add_step(
                SetInitialVolume(
                    plate=plate, section_index=plate_section_index, column_index=destination_column_index, volume=0
                )
            )

        kwargs: dict[str, Any] = {
            kwarg_name: value
            for value, kwarg_name in [
                (aspirate_params, "aspirate_parameters"),
                (dispense_params, "dispense_parameters"),
                (tip_change_mode, "tip_change_mode"),
                (reverse_pipetting_volume, "reverse_pipetting_volume"),
                (pre_dispense_volume, "pre_dispense_volume"),
            ]
            if value is not None
        }

        program.add_step(
            MultiDispense(
                source=PipettingLocation(
                    labware=plate,
                    deck_section_index=plate_section_index,
                    column_index=source_column_index,
                    upper_left_row_index=0,
                ),
                destinations=[
                    (
                        PipettingLocation(
                            labware=plate,
                            deck_section_index=plate_section_index,
                            column_index=destination_column_index,
                            upper_left_row_index=0,
                        ),
                        volume,
                    )
                    for destination_column_index, volume in destination_column_indexes_and_volumes
                ],
                **kwargs,
            )
        )

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / f"{uuid.uuid1()}simple-transfer.iaa"
            program.dump_xml(file_path)
            xml_str = file_path.read_text()

        assert xml_str == self.snapshot_xml
