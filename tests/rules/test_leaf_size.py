import unittest

from ccf.pylib.dimension import Dimension
from ccf.rules.leaf_size import LeafSize
from ccf.rules.size import Size
from tests.setup import parse


class TestLeafSize(unittest.TestCase):
    def test_leaf_size_01(self):
        self.assertEqual(
            parse(
                """
                Leaves petioles (5–)10–30(–50) mm; 4–11(–13) × 2.5–8(–9) cm
                """
            ),
            [
                Size(
                    start=35,
                    end=59,
                    dims=[
                        Dimension(
                            dim="length",
                            units="cm",
                            low=4.0,
                            high=11.0,
                            max=13.0,
                            start=35,
                            end=44,
                        ),
                        Dimension(
                            dim="width",
                            units="cm",
                            low=2.5,
                            high=8.0,
                            max=9.0,
                            start=47,
                            end=59,
                        ),
                    ],
                ),
            ],
        )

    def test_leaf_size_02(self):
        self.assertEqual(
            parse(
                """
                Basal leaves: (petioles 12–18+ cm) blades (lateral veins appressed
                to midveins 2–4 cm, then spreading), 15–37 cm
                """
            ),
            [
                Size(
                    start=104,
                    end=112,
                    dims=[
                        Dimension(
                            dim="length",
                            units="cm",
                            low=15.0,
                            high=37.0,
                            start=104,
                            end=112,
                        )
                    ],
                ),
            ],
        )

    def test_leaf_size_03(self):
        self.assertEqual(
            parse("""Leaf blades, 13–37 × 7–32 mm,"""),
            [
                Size(
                    start=13,
                    end=28,
                    dims=[
                        Dimension(
                            dim="length",
                            units="mm",
                            low=13,
                            high=37,
                            start=13,
                            end=18,
                        ),
                        Dimension(
                            dim="width",
                            units="mm",
                            low=7,
                            high=32,
                            start=21,
                            end=28,
                        ),
                    ],
                )
            ],
        )

    def test_leaf_size_04(self):
        self.assertEqual(
            parse("""Leaf blades 13–37 × 7–32 mm,"""),
            [
                LeafSize(
                    start=0,
                    end=27,
                    part="leaf",
                    dims=[
                        Dimension(
                            dim="length",
                            units="mm",
                            low=13,
                            high=37,
                            start=12,
                            end=17,
                        ),
                        Dimension(
                            dim="width",
                            units="mm",
                            low=7,
                            high=32,
                            start=20,
                            end=27,
                        ),
                    ],
                )
            ],
        )
