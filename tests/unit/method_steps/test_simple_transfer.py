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
from ..fixtures import arbitrary_d_one_program_framework
from ..fixtures import generate_xml_str


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
        pcr_plate_section_index = program.get_section_index_for_labware(pcr_plate)

        program.add_step(
            SetInitialVolume(
                labware=pcr_plate,
                section_index=pcr_plate_section_index,
                column_index=source_column_index,
                volume=starting_volume,
            )
        )
        program.add_step(
            SetInitialVolume(
                labware=pcr_plate,
                section_index=pcr_plate_section_index,
                column_index=destination_column_index,
                volume=0,
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

        assert generate_xml_str(program) == self.snapshot_xml


class TestDOneSimpleTransfer(ProgramSnapshot):
    def test_Given_single_tip_type(self):
        program = arbitrary_d_one_program_framework()
        labware = program.the_labware
        assert isinstance(labware, Plate)
        pcr_plate_section_index = program.get_section_index_for_labware(labware)
        source_column_index = 5
        source_row_index = 1
        destination_column_index = 2
        destination_row_index = 3
        program.add_step(
            SetInitialVolume(
                volume=25,
                column_index=source_column_index,
                labware=labware,
                section_index=pcr_plate_section_index,
                row_index=source_row_index,
            )
        )
        program.add_step(
            SetInitialVolume(
                volume=0,
                labware=labware,
                section_index=pcr_plate_section_index,
                column_index=destination_column_index,
                row_index=destination_row_index,
            )
        )

        program.add_step(
            Transfer(
                source=labware,
                source_section_index=pcr_plate_section_index,
                source_column_index=source_column_index,
                source_row_index=source_row_index,
                destination=labware,
                destination_section_index=pcr_plate_section_index,
                destination_column_index=destination_column_index,
                destination_row_index=destination_row_index,
                volume=12.5,
            )
        )

        assert generate_xml_str(program) == self.snapshot_xml
