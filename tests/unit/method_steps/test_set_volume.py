import random

import pytest
from pydantic import ValidationError

from pyalab import Plate
from pyalab import SetVolume


class TestDataValidation:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.generic_plate = Plate(name="BIO-RAD Hard-Shell 96-Well Skirted PCR Plates")

    def test_When_negative_volume__Then_error(self):
        expected_volume = -0.1

        with pytest.raises(ValidationError, match=rf"volume(.|\n)*greater(.|\n)*{expected_volume}"):
            _ = SetVolume(labware=self.generic_plate, column_index=random.randint(0, 11), volume=expected_volume)
