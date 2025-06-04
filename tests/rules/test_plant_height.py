import unittest

from ccf.pylib.dimension import Dimension
from ccf.rules.size import Size
from tests.setup import parse


class TestPlantHeight(unittest.TestCase):
    def test_plant_height_01(self):
        self.assertEqual(
            parse("""Herbs, bulbous-based, (5–)10–50(–70) cm."""),
            [
                Size(
                    start=22,
                    end=40,
                    dims=[
                        Dimension(
                            dim="length",  # is used as height
                            units="cm",
                            min=5.0,
                            low=10.0,
                            high=50.0,
                            max=70.0,
                            start=22,
                            end=40,
                        )
                    ],
                ),
            ],
        )

    def test_plant_height_02(self):
        self.assertEqual(
            parse("""Herbs, perennial, cespitose; rhizomes 0.5–2 cm, often absent."""),
            [],
        )

    def test_plant_height_03(self):
        self.assertEqual(
            parse("""thickened taproot, 5 mm diam."""),
            [],
        )

    def test_plant_height_04(self):
        self.assertEqual(
            parse("""rhizome rhizome internodes 1.2–2.8 mm thick."""),
            [],
        )

    def test_plant_height_05(self):
        self.assertEqual(
            parse("""with knotty rhizomes less than 2 mm thick."""),
            [],
        )
