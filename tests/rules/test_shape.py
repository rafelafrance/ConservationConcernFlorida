import unittest

from ccf.rules.shape import Shape
from tests.setup import parse


class TestShape(unittest.TestCase):
    def test_shape_01(self):
        self.assertEqual(
            parse("""Leaf blades deltate to ± rhombic or ovate,"""),
            [
                Shape(start=12, end=19, shape="deltate"),
                Shape(start=25, end=32, shape="rhombic"),
                Shape(start=36, end=41, shape="ovate"),
            ],
        )
