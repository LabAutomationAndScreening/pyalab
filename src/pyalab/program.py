import json
import re
import uuid
from copy import deepcopy
from functools import cached_property
from pathlib import Path
from typing import Any
from typing import override
from xml.dom import minidom

from lxml import etree
from pydantic import BaseModel
from pydantic import Field

from .deck import DeckLayout
from .integra_xml import NS_XSI
from .pipette import DOneTips
from .pipette import Pipette
from .pipette import Tip
from .plate import Labware
from .steps import Step


class InvalidTipInputFormatError(Exception):
    def __init__(self, *, pipette_is_d_one: bool):
        super().__init__(
            f"When a program uses a {'' if pipette_is_d_one else 'non-'}D-ONE pipette, you must define the tips using the '{DOneTips.__name__ if pipette_is_d_one else Tip.__name__}' object, not the '{Tip.__name__ if pipette_is_d_one else DOneTips.__name__}' object"
        )


class LabwareNotInDeckLayoutError(Exception):
    def __init__(self, labware: Labware):
        super().__init__(f"Could not find {labware.name} (called {labware.display_name}) in the deck layout")


class Program(BaseModel):
    deck_layouts: list[DeckLayout] = Field(min_length=1)  # TODO: validate that all layouts use the same base Deck
    display_name: str  # TODO: validate length and character classes
    description: str  # TODO: validate length and character classes
    pipette: Pipette
    tip: Tip | DOneTips
    steps: list[Step] = Field(default_factory=list)

    @override
    def model_post_init(self, _: Any) -> None:
        if self.is_d_one and isinstance(self.tip, Tip):
            raise InvalidTipInputFormatError(pipette_is_d_one=True)
        if not self.is_d_one and isinstance(self.tip, DOneTips):
            raise InvalidTipInputFormatError(pipette_is_d_one=False)

    @property
    def the_labware(self) -> Labware:
        # useful for unit testing simple programs that only have a single labware
        assert len(self.deck_layouts) == 1
        deck_layout = self.deck_layouts[0]
        assert len(deck_layout.labware) == 1, (
            f"DeckLayout should only have one labware for this to be used, but found {len(deck_layout.labware)}"
        )
        return next(iter(deck_layout.labware.values()))

    @cached_property
    def is_d_one(self) -> bool:
        return self.pipette.is_d_one

    def add_step(self, step: Step) -> None:
        step.set_pipette(self.pipette)
        if isinstance(self.tip, DOneTips):
            if self.tip.second_available_position is not None:
                raise NotImplementedError("Adding steps with two different D-One tip types is not implemented yet")
            step.set_tip(self.tip.first_available_position)
        else:
            step.set_tip(self.tip)

        self.steps.append(step)

    def get_section_index_for_labware(self, labware: Labware) -> int:
        # TODO: support multiple deck layouts
        first_deck_layout = self.deck_layouts[0]
        for deck_position, iter_plate in first_deck_layout.labware.items():
            if iter_plate == labware:
                return deck_position.section_index(deck=first_deck_layout.deck, labware=labware)

        raise LabwareNotInDeckLayoutError(labware)

    def generate_xml(self) -> str:
        config_version = 4
        data_version = 9
        root = etree.Element(
            "AssistConfig",
            nsmap={"xsd": "http://www.w3.org/2001/XMLSchema", "xsi": NS_XSI},
            UniqueIdentifier=str(uuid.uuid4()),
            Version=str(config_version),
        )

        for element_name, text_value in [
            ("MigrationIdentifier", str(uuid.uuid4())),
            ("CreatedWith", f"PyaLab for VIALAB v3.4.0.0, config v{config_version}, data v{data_version}"),
            ("CreatedBy", "UnknownUser"),
            ("MigrationHistory", ""),
            ("DataVersion", str(data_version)),
            ("DisplayNameOnPipette", self.display_name),
            ("Description", self.description),
        ]:
            etree.SubElement(root, element_name).text = text_value

        root.append(self.pipette.create_xml_for_program())
        tip_to_append_to_root: Tip
        # When both positions are set when using D-ONE, it doesn't seem to matter which one is used as the first `Tip` section in the XML
        tip_to_append_to_root = self.tip if isinstance(self.tip, Tip) else self.tip.first_available_position
        tip_to_append_to_root_xml = tip_to_append_to_root.create_xml_for_program()
        if self.is_d_one:
            assert isinstance(self.tip, DOneTips)
            if self.tip.position_2 is None:
                # This seems related to telling Vialab that the tip box should be in the "1" (left) position of the D-ONE tip adapter...Vialab seems to treat the "2" (right) position the same as a normal tip box
                _ = etree.SubElement(tip_to_append_to_root_xml, "TipSpecial", attrib={f"{{{NS_XSI}}}nil": "true"})
        root.append(deepcopy(tip_to_append_to_root_xml))
        tips_node = etree.SubElement(root, "Tips")
        tips_node.append(deepcopy(tip_to_append_to_root_xml))
        if self.is_d_one:
            assert isinstance(self.tip, DOneTips)
            if self.tip.second_available_position is not None:
                tips_node.append(self.tip.second_available_position.create_xml_for_program())

        # TODO: handle multiple deck layouts
        first_deck_layout = self.deck_layouts[0]
        root.append(first_deck_layout.create_xml_for_program(layout_num=1))
        decks_node = etree.SubElement(root, "AllDecks")
        decks_node.append(first_deck_layout.create_xml_for_program(layout_num=1))

        steps_node = etree.SubElement(root, "Steps")
        for step in self.steps:
            steps_node.append(step.create_xml_for_program())

        global_parameters_node = etree.SubElement(root, "GlobalParameters", attrib={"Key": "Global"})
        global_parameters_value_node = etree.SubElement(global_parameters_node, "Values")
        for key, value in [
            ("ClearanceHeight", 800),
            ("SectionOffsets", "null"),
            ("DisplayTipEjectionOptions", "true"),
            ("AfterTipEjectMonitoring", "true"),
            ("AfterTipLoadMonitoring", "false"),
            ("BeforeTipEjectMonitoring", "true"),
            (
                "TipTypeRequiredTips",
                json.dumps(
                    {
                        str(
                            tip_to_append_to_root.tip_id
                        ): 0  # there seems to be no negative impact of not calculating the required tips, Vialab will do it automatically when the program is first loaded
                    }
                ),
            ),
            ("WasteAsTargetOption", "false"),
            ("LabwareReintegration", "false"),
            ("CopyHeightAdjustment", "false"),
            ("WellBottomMinHeight", 200),
            ("CollisionAvoidanceOffset", 0),
            ("CollisionDetection", "true"),
        ]:
            etree.SubElement(global_parameters_value_node, "Value", attrib={"Key": key}).text = (
                etree.CDATA(str(value)) if '"' in str(value) else str(value)
            )

        _ = etree.SubElement(root, "ChangedDate").text = (
            "2024-12-17T16:27:27.0715524-05:00"  # TODO: make this real time
        )
        _ = etree.SubElement(root, "LastChangeUser").text = "UnknownUser"

        xml_string = etree.tostring(root, xml_declaration=True, encoding="utf-8")
        xml_str = minidom.parseString(xml_string).toprettyxml(indent="  ")  # noqa: S318 # it is safe to parse this string because it is generated by the program
        xml_str_cleaned = re.sub(r"\n\s*\n", "\n", xml_str)
        return xml_str_cleaned.replace(
            '<?xml version="1.0" ?>', '<?xml version="1.0" encoding="utf-8"?>'
        )  # TODO: figure out why the encoding argument to `tostring` isn't working as expected

    def dump_xml(self, file_path: Path) -> None:
        # TODO: deprecate this
        xml_str = self.generate_xml()
        _ = file_path.write_text(xml_str)

    def save_program(self, file_path: Path) -> None:
        self.dump_xml(file_path)
