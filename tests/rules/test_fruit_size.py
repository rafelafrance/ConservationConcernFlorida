import unittest

from ccf.pylib.dimension import Dimension
from ccf.rules.fruit_size import FruitSize
from ccf.rules.size import Size
from tests.setup import parse


class TestFruitSize(unittest.TestCase):
    def test_fruit_size_01(self):
        self.assertEqual(
            parse("""Fruits strongly compressed, ± cuneate, 2–3(–4) mm,"""),
            [
                Size(
                    start=39,
                    end=49,
                    units="cm",
                    dims=[
                        Dimension(
                            dim="length",
                            units="mm",
                            low=0.2,
                            high=0.3,
                            max=0.4,
                        )
                    ],
                ),
            ],
        )

    def test_fruit_size_02(self):
        self.assertEqual(
            parse("""Fruits 2–3(–4) mm,"""),
            [
                FruitSize(
                    start=0,
                    end=17,
                    part="fruit",
                    units="cm",
                    dims=[
                        Dimension(
                            dim="length",
                            units="mm",
                            low=0.2,
                            high=0.3,
                            max=0.4,
                        )
                    ],
                ),
            ],
        )

    def test_fruit_size_03(self):
        self.assertEqual(
            parse("""Beaks 2–3(–4) mm,"""),
            [
                FruitSize(
                    start=0,
                    end=16,
                    part="beak",
                    units="cm",
                    dims=[
                        Dimension(
                            dim="length",
                            units="mm",
                            low=0.2,
                            high=0.3,
                            max=0.4,
                        )
                    ],
                ),
            ],
        )
