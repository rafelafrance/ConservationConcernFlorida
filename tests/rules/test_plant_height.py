import unittest

from ccf.pylib.dimension import Dimension
from ccf.rules.size import Size
from tests.setup import parse


class TestFruitSize(unittest.TestCase):
    def test_fruit_size_01(self):
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
