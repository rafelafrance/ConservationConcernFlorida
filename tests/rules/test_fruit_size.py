import unittest

from ccf.pylib.dimension import Dimension
from ccf.rules.fruit_size import FruitSize
from ccf.rules.size import Size
from tests.setup import parse


class TestFruitSize(unittest.TestCase):
    def test_fruit_size_01(self):
        self.assertEqual(
            parse("""Fruits strongly compressed, 2–3(–4) mm,"""),
            [
                Size(
                    start=28,
                    end=38,
                    dims=[
                        Dimension(
                            dim="length",
                            units="mm",
                            low=2.0,
                            high=3.0,
                            max=4.0,
                            start=28,
                            end=38,
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
                    dims=[
                        Dimension(
                            dim="length",
                            units="mm",
                            low=2.0,
                            high=3.0,
                            max=4.0,
                            start=7,
                            end=17,
                        )
                    ],
                ),
            ],
        )

    def test_fruit_size_03(self):
        self.assertEqual(
            parse("""Beaks 2–3(–4) mm,"""),
            [],
        )
