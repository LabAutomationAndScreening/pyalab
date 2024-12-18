.. _example:

Example Program
===============
This simple example demonstrates using loops and variables to transfer between wells.
    .. code-block:: py
        :caption: example.py

        from pathlib import Path
        from pyalab import Deck, DeckLayout, DeckPositions, Pipette, Plate, Program, SetInitialVolume, SetVolume, StandardDeckNames, Tip, Transfer

        pcr_plate = Plate(name="BIO-RAD Hard-Shell 96-Well Skirted PCR Plates", display_name="PCR Plate")
        program = Program(
            deck_layouts=[
                DeckLayout(
                    deck=Deck(name=StandardDeckNames.THREE_POSITION.value),
                    labware={DeckPositions.B_PLATE_LANDSCAPE.value: pcr_plate},
                )
            ],
            display_name="simple-transfer",
            description="Transfer in 96-well plate",
            pipette=Pipette(name="VOYAGER EIGHT 300 µl"),
            tip=Tip(name="300 µl GripTip Sterile Filter Low retention"),
        )
        pcr_plate_section_index = program.get_section_index_for_plate(pcr_plate)

        program.add_step(
            SetInitialVolume(
                plate=pcr_plate,
                section_index=pcr_plate_section_index,
                column_index=0,
                volume=200,
            )
        )
        for column_index in range(1, 12):
            program.add_step(
                SetVolume(
                    plate=pcr_plate,
                    section_index=pcr_plate_section_index,
                    column_index=column_index,
                    volume=0,
                )
            )

        transfer_volume = 18
        for column_index in range(1, 12):
            program.add_step(
                Transfer(
                    source=pcr_plate,
                    source_section_index=pcr_plate_section_index,
                    source_column_index=0,
                    destination=pcr_plate,
                    destination_section_index=pcr_plate_section_index,
                    destination_column_index=column_index,
                    volume=transfer_volume,
                )
            )
            transfer_volume -= 1
        program.dump_xml(Path(__file__).parent / "simple-transfer.iaa")
