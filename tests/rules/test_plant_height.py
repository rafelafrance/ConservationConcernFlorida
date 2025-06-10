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

    def test_plant_height_06(self):
        self.assertEqual(
            parse("""Herbs, annual or perennial, 2–6 dm."""),
            [
                Size(
                    start=28,
                    end=35,
                    dims=[
                        Dimension(
                            dim="length",  # is used as height
                            units="dm",
                            low=2.0,
                            high=6.0,
                            start=28,
                            end=35,
                        )
                    ],
                ),
            ],
        )

    def test_plant_height_07(self):
        self.assertEqual(
            parse("""hairs erect, 1–2 mm;"""),
            [],
        )

    def test_plant_height_08(self):
        self.assertEqual(
            parse(
                """hairs simple, jointed, 0.5–1 mm,
                intermixed with glands to 0.5 mm"""
            ),
            [],
        )

    def test_plant_height_09(self):
        self.assertEqual(
            parse("""hairs unbranched, to 1 mm,"""),
            [],
        )

    def test_plant_height_10(self):
        self.assertEqual(
            parse("""Culms 60-100 (150) cm,"""),
            [
                Size(
                    start=6,
                    end=21,
                    dims=[
                        Dimension(
                            dim="length",
                            units="cm",
                            low=60.0,
                            high=100.0,
                            max=150.0,
                            start=6,
                            end=21,
                        )
                    ],
                ),
            ],
        )

    def test_plant_height_11(self):
        self.assertEqual(
            parse("""Culms 1-2(4) m tall, 3-5 mm thick, clumped."""),
            [
                Size(
                    start=6,
                    end=19,
                    dims=[
                        Dimension(
                            dim="height",
                            units="m",
                            low=1.0,
                            high=2.0,
                            max=4.0,
                            start=6,
                            end=19,
                        )
                    ],
                ),
                Size(
                    start=21,
                    end=33,
                    dims=[
                        Dimension(
                            dim="thickness",
                            units="mm",
                            low=3.0,
                            high=5.0,
                            start=21,
                            end=33,
                        )
                    ],
                ),
            ],
        )

    def test_plant_height_12(self):
        self.assertEqual(
            parse("""Culms (20)30-130(150) cm."""),
            [
                Size(
                    start=6,
                    end=25,
                    dims=[
                        Dimension(
                            dim="length",
                            units="cm",
                            min=20.0,
                            low=30.0,
                            high=130.0,
                            max=150.0,
                            start=6,
                            end=25,
                        )
                    ],
                )
            ],
        )
