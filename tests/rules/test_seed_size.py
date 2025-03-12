import unittest

from ccf.pylib.dimension import Dimension
from ccf.rules.seed_size import SeedSize
from tests.setup import parse


class TestSeedSize(unittest.TestCase):
    def test_seed_size_02(self):
        self.assertEqual(
            parse("""Seeds 2–3(–4) mm,"""),
            [
                SeedSize(
                    start=0,
                    end=16,
                    part="seed",
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

    def test_seed_size_03(self):
        self.assertEqual(
            parse("""hila 2–3(–4) mm,"""),
            [
                SeedSize(
                    start=0,
                    end=15,
                    part="hilum",
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
