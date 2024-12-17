from typing import ClassVar

from lxml import etree
from lxml.etree import _Element
from pydantic import BaseModel


class Step(BaseModel):
    type: ClassVar[str]

    def create_xml_for_program(self) -> _Element:
        root = etree.Element("Step")
        etree.SubElement(root, "Type").text = self.type
        return root


class SetVolume(Step):
    type = "ManualFilling_First"
