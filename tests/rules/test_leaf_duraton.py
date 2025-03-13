import unittest

from ccf.rules.leaf_duration import LeafDuration
from tests.setup import parse


class TestLeafDuration(unittest.TestCase):
    def test_leaf_duration_01(self):
        self.assertEqual(
            parse("""Plants deciduous to evergreen by production of new growth,"""),
            [
                LeafDuration(start=7, end=16, leaf_duration="deciduous"),
                LeafDuration(start=20, end=29, leaf_duration="evergreen"),
            ],
        )
