from enum import Enum

from pydantic import BaseModel

from pyalab.plate import Labware
from pyalab.steps.base import LiquidMovementParameters


class TipChangeMode(Enum):
    NO_CHANGE = "TipChange_Never"
    AFTER_STEP = "TipChange_AfterStep"
    MODE_A = "TipChange_ModeA"  # Transfer uses this...unclear what it is


class PipettingLocation(BaseModel, frozen=True):
    labware: Labware
    """The labware to pipette from or to."""
    deck_section_index: int
    """The deck section index to pipette from or to."""
    column_index: int
    """The column index to pipette from or to for the pipette tip that is at the rear of the instrument."""
    upper_left_row_index: int
    """The row index of the pipette tip that is at the rear of the instrument."""
    # TODO: handle different tip spacing


class AspirateParameters(LiquidMovementParameters, frozen=True):
    pass


class DispenseParameters(LiquidMovementParameters, frozen=True):
    pass
