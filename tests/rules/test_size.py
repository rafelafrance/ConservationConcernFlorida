import unittest

from ccf.rules.size import Dimension, Size
from tests.setup import parse


class TestSize(unittest.TestCase):
    def test_size_01(self):
        """It handles values larger than 1000."""
        self.assertEqual(
            parse("""Elevation: 0–3600 m"""),
            [
                Size(
                    dims=[Dimension(dim="length", low=0, high=360000, units="m")],
                    start=11,
                    end=19,
                    units="cm",
                ),
            ],
        )

    def test_size_02(self):
        """It handles too many numbers."""
        self.assertEqual(
            parse("""(10–)30–60(–180+)[–250] cm"""),
            [
                Size(
                    dims=[
                        Dimension(
                            dim="length", min=10, low=30, high=60, max=180, units="cm"
                        )
                    ],
                    start=0,
                    end=26,
                    units="cm",
                ),
            ],
        )

    def test_size_03(self):
        """It handles an extra plus sign."""
        self.assertEqual(
            parse("""(5–)10–30+[–80] cm"""),
            [
                Size(
                    dims=[
                        Dimension(
                            dim="length", min=5, low=10, high=30, max=80, units="cm"
                        )
                    ],
                    start=0,
                    end=18,
                    units="cm",
                ),
            ],
        )
