import unittest

from ccf.rules.surface import Surface
from tests.setup import parse


class TestSurface(unittest.TestCase):
    def test_surface_01(self) -> None:
        self.assertEqual(
            parse("""glabrous flowers"""),
            [Surface(surface="glabrous", start=0, end=8)],
        )
