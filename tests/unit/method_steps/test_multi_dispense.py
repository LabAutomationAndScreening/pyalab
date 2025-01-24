import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import pytest

from pyalab import Deck
from pyalab import DeckLayout
from pyalab import DeckPosition
from pyalab import DispenseParameters
from pyalab import LabwareOrientation
from pyalab import Pipette
from pyalab import Program
from pyalab import SetInitialVolume
from pyalab import StandardDeckNames
from pyalab import Tip
from pyalab import Transfer
from pyalab.steps.params import AspirateParameters

from ..constants import GENERIC_96_DEEP_WELL_PLATE
from ..fixtures import ProgramSnapshot


class TestMultiDispenseProgramSnapshots(ProgramSnapshot):
    @pytest.mark.parametrize(
        (
            "source_column_index",
            "destination_column_indexes",
            "aspirate_params",
            "dispense_params",
        ),
        [
            pytest.param(
                3,
                [8],
                None,
                None,
                id="arbitrary1",
            )
        ],
    )
    def test_arbitrary_params(  # noqa: PLR0913 # this is a lot of arguments to parametrize, but it makes it more efficient to not generate a bunch of separate snapshot files
        self,
        source_column_index: int,
        destination_column_indexes: list[int],
        # use None to test not providing that kwarg to test the default value behavior
        aspirate_params: AspirateParameters | None,
        dispense_params: DispenseParameters | None,
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
        for destination_column_index in destination_column_indexes:
            program.add_step(
                SetInitialVolume(
                    plate=plate, section_index=plate_section_index, column_index=destination_column_index, volume=0
                )
            )

        kwargs: dict[str, Any] = {}
        if aspirate_params is not None:
            kwargs["aspirate_parameters"] = aspirate_params
        if dispense_params is not None:
            kwargs["dispense_parameters"] = dispense_params

        program.add_step(
            Transfer(
                source=pcr_plate,
                source_section_index=plate_section_index,
                source_column_index=source_column_index,
                destination=pcr_plate,
                destination_section_index=plate_section_index,
                destination_column_index=destination_column_index,
                volume=transfer_volume,
                **kwargs,
            )
        )

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / f"{uuid.uuid1()}simple-transfer.iaa"
            program.dump_xml(file_path)
            xml_str = file_path.read_text()

        assert xml_str == self.snapshot_xml
