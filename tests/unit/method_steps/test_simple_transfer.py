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
from pyalab import Plate
from pyalab import Program
from pyalab import SetInitialVolume
from pyalab import StandardDeckNames
from pyalab import Tip
from pyalab import Transfer
from pyalab.steps.params import AspirateParameters

from ..fixtures import ProgramSnapshot


class TestSimpleTransferProgramSnapshots(ProgramSnapshot):
    @pytest.mark.parametrize(
        (
            "source_column_index",
            "destination_column_index",
            "starting_volume",
            "transfer_volume",
            "display_name",
            "description",
            "tip",
            "aspirate_params",
            "dispense_params",
        ),
        [
            pytest.param(
                3,
                8,
                100,
                50,
                "simple-transfer",
                "One transfer within a 96-well plate",
                Tip(name="300 µl GripTip Sterile Filter Low retention"),
                None,
                DispenseParameters(start_height=5),
                id="arbitrary1",
            ),
            pytest.param(
                5,
                1,
                132.21,
                37.5,
                "wakka_wakka",
                "doing science!",
                Tip(name="300 µl GripTip Sterile Filter"),
                AspirateParameters(start_height=2),
                None,
                id="arbitrary2",
            ),
        ],
    )
    def test_arbitrary_params(  # noqa: PLR0913 # this is a lot of arguments to parametrize, but it makes it more efficient to not generate a bunch of separate snapshot files
        self,
        source_column_index: int,
        destination_column_index: int,
        starting_volume: float,
        transfer_volume: float,
        display_name: str,
        description: str,
        tip: Tip,
        # use None to test not providing that kwarg to test the default value behavior
        aspirate_params: AspirateParameters | None,
        dispense_params: DispenseParameters | None,
    ):
        pcr_plate = Plate(name="BIO-RAD Hard-Shell 96-Well Skirted PCR Plates", display_name="PCR Plate")
        program = Program(
            deck_layouts=[
                DeckLayout(
                    deck=Deck(name=StandardDeckNames.THREE_POSITION.value),
                    labware={DeckPosition(name="B", orientation=LabwareOrientation.A1_NW_CORNER): pcr_plate},
                )
            ],
            display_name=display_name,
            description=description,
            pipette=Pipette(name="VOYAGER EIGHT 300 µl"),
            tip=tip,
        )
        pcr_plate_section_index = program.get_section_index_for_plate(pcr_plate)

        program.add_step(
            SetInitialVolume(
                plate=pcr_plate,
                section_index=pcr_plate_section_index,
                column_index=source_column_index,
                volume=starting_volume,
            )
        )
        program.add_step(
            SetInitialVolume(
                plate=pcr_plate, section_index=pcr_plate_section_index, column_index=destination_column_index, volume=0
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
                source_section_index=pcr_plate_section_index,
                source_column_index=source_column_index,
                destination=pcr_plate,
                destination_section_index=pcr_plate_section_index,
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
