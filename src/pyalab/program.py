import json
import re
import uuid
from pathlib import Path
from xml.dom import minidom

from lxml import etree
from pydantic import BaseModel
from pydantic import Field

from .deck import DeckLayout
from .pipette import Pipette
from .pipette import Tip
from .plate import Labware
from .steps import Step


class LabwareNotInDeckLayoutError(Exception):
    def __init__(self, labware: Labware):
        super().__init__(f"Could not find {labware.name} (called {labware.display_name}) in the deck layout")


class Program(BaseModel):
    deck_layouts: list[DeckLayout] = Field(min_length=1)  # TODO: validate that all layouts use the same base Deck
    display_name: str  # TODO: validate length and character classes
    description: str  # TODO: validate length and character classes
    pipette: Pipette
    tip: Tip
    steps: list[Step] = Field(default_factory=list)

    def add_step(self, step: Step) -> None:
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
            nsmap={"xsd": "http://www.w3.org/2001/XMLSchema", "xsi": "http://www.w3.org/2001/XMLSchema-instance"},
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
        root.append(self.tip.create_xml_for_program())
        tips_node = etree.SubElement(root, "Tips")
        # TODO: figure out how to handle multiple tip types, likely for the D-ONE
        tips_node.append(self.tip.create_xml_for_program())

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
                            self.tip.tip_id
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
        xml_str = self.generate_xml()
        _ = file_path.write_text(xml_str)
