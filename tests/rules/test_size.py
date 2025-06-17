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
                    dims=[
                        Dimension(
                            dim="length",
                            low=0,
                            high=3600,
                            units="m",
                            start=11,
                            end=19,
                        )
                    ],
                    start=11,
                    end=19,
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
                            dim="length",
                            min=10,
                            low=30,
                            high=60,
                            max=180,
                            units="cm",
                            start=0,
                            end=26,
                        )
                    ],
                    start=0,
                    end=26,
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
                            dim="length",
                            min=5,
                            low=10,
                            high=30,
                            max=80,
                            units="cm",
                            start=0,
                            end=18,
                        )
                    ],
                    start=0,
                    end=18,
                ),
            ],
        )

    def test_size_04(self):
        """It handles a width only notation."""
        self.assertEqual(
            parse("""0.8–2.5 mm wide"""),
            [
                Size(
                    dims=[
                        Dimension(
                            dim="width",
                            low=0.8,
                            high=2.5,
                            units="mm",
                            start=0,
                            end=15,
                        )
                    ],
                    start=0,
                    end=15,
                ),
            ],
        )

    def test_size_05(self):
        self.maxDiff = None
        self.assertEqual(
            parse("""(2.5-)2.8-3.5(-4.5) × 1x 1.6-2.2 mm"""),
            [
                Size(
                    start=0,
                    end=35,
                    dims=[
                        Dimension(
                            dim="length",
                            units="mm",
                            min=2.5,
                            low=2.8,
                            high=3.5,
                            max=4.5,
                            start=0,
                            end=19,
                        ),
                        Dimension(
                            dim="width",
                            units="mm",
                            low=1.0,
                            start=22,
                            end=23,
                        ),
                        Dimension(
                            dim="thickness",
                            units="mm",
                            low=1.6,
                            high=2.2,
                            start=25,
                            end=35,
                        ),
                    ],
                )
            ],
        )
