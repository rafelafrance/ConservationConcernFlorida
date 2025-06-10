import unittest

from ccf.rules.shape import Shape
from tests.setup import parse


class TestShape(unittest.TestCase):
    def test_shape_01(self):
        self.assertEqual(
            parse("""Leaf blades deltate to ± rhombic or ovate,"""),
            [
                Shape(start=12, end=19, shape="deltate"),
                Shape(start=27, end=34, shape="rhombic"),
                Shape(start=38, end=43, shape="ovate"),
            ],
        )
