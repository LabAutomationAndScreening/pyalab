import json
from abc import ABC
from typing import Any

from pyalab.plate import Labware

from .base import Step
from .params import TipChangeMode


class StepWithPipetteSpan(Step, ABC):
    pipette_span: float | None = None
    """Override the default well-to-well spacing of the labware."""

    def _pipette_span(self, labware: Labware) -> float:
        pipette_span = self.pipette_span
        if pipette_span is None:
            pipette_span = labware.row_spacing()  # TODO: handle spacing based on landscape vs portrait orientation
        return pipette_span


class LiquidTransferStep(StepWithPipetteSpan, ABC):
    tip_change_mode: TipChangeMode

    def _add_tips_value_group(self) -> None:
        self._add_value_group(
            group_name="Tips",
            values=[
                ("PreWetting", json.dumps(obj=False)),
                ("PreWettingCycles", json.dumps(obj=3)),
                ("TipChange", json.dumps(self.tip_change_mode.value)),
                ("TipEjectionType", json.dumps(obj=True)),
            ],
        )

    def _add_tip_touch_target_group(self, deck_section_model_dict: dict[str, Any]) -> None:
        self._add_value_group(
            group_name="TipTouchTarget",
            values=[
                ("TipTouchActive", json.dumps(obj=False)),
                (
                    "SectionTipTouch",
                    json.dumps(
                        obj=[
                            {
                                **deck_section_model_dict,
                                "Type": False,
                                "Height": 1406,  # TODO: implement tip touch
                                "Distance": 225,
                            }
                        ]
                    ),
                ),
            ],
        )
