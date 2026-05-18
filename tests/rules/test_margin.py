import unittest

from ccf.rules.margin import Margin
from ccf.rules.shape import Shape
from tests.setup import parse


class TestMargin(unittest.TestCase):
    def test_margin_01(self) -> None:
        self.assertEqual(
            parse("margin shallowly undulate-crenate"),
            [
                Margin(margin="shallowly undulate-crenate", start=7, end=33),
            ],
        )

    def test_margin_02(self) -> None:
        """It removes unattached margins."""
        self.assertEqual(
            parse("reniform, undulate-margined"),
            [
                Shape(shape="reniform", start=0, end=8),
                Margin(margin="undulate-margined", start=10, end=27),
            ],
        )

    def test_margin_03(self) -> None:
        self.assertEqual(
            parse("margins thickened-corrugated"),
            [
                Margin(margin="thickened-corrugated", start=8, end=28),
            ],
        )

    def test_margin_04(self) -> None:
        self.assertEqual(
            parse("margins coarsely toothed or remotely sinuate-dentate to serrate,"),
            [
                Margin(margin="coarsely toothed", start=8, end=24),
                Margin(margin="remotely sinuate-dentate", start=28, end=52),
                Margin(margin="serrate", start=56, end=63),
            ],
        )
