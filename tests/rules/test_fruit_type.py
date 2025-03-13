import unittest

from ccf.rules.fruit_type import FruitType
from tests.setup import parse


class TestFruitType(unittest.TestCase):
    def test_fruit_type_01(self):
        self.assertEqual(
            parse("""Cypselae usually tan to brown"""),
            [
                FruitType(start=0, end=8, fruit_type="cypsela"),
            ],
        )
