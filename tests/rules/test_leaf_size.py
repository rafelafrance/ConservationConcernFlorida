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
                Leaves petioles (5–)10–30(–50) mm;
                sometimes ovate-lanceolate, 4–11(–13) × 2.5–8(–9) cm
                """
            ),
            [
                LeafSize(
                    start=7,
                    end=33,
                    part="petiole",
                    dims=[
                        Dimension(
                            dim="length",
                            units="mm",
                            min=5,
                            low=10,
                            high=30,
                            max=50,
                            start=16,
                            end=33,
                        )
                    ],
                ),
                Size(
                    start=63,
                    end=87,
                    dims=[
                        Dimension(
                            dim="length",
                            units="cm",
                            low=4.0,
                            high=11.0,
                            max=13.0,
                            start=63,
                            end=72,
                        ),
                        Dimension(
                            dim="width",
                            units="cm",
                            low=2.5,
                            high=8.0,
                            max=9.0,
                            start=75,
                            end=87,
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
                to midveins 2–4 cm, then spreading) oblong-lanceolate, 15–37 cm
                """
            ),
            [
                LeafSize(
                    start=15,
                    end=33,
                    part="petiole",
                    dims=[
                        Dimension(
                            dim="length",
                            units="cm",
                            low=12.0,
                            high=18.0,
                            start=24,
                            end=33,
                        )
                    ],
                ),
                LeafSize(
                    start=70,
                    end=85,
                    part="midrib",
                    dims=[
                        Dimension(
                            dim="length",
                            units="cm",
                            low=2.0,
                            high=4.0,
                            start=79,
                            end=85,
                        )
                    ],
                ),
                Size(
                    start=122,
                    end=130,
                    dims=[
                        Dimension(
                            dim="length",
                            units="cm",
                            low=15.0,
                            high=37.0,
                            start=122,
                            end=130,
                        )
                    ],
                ),
            ],
        )

    def test_leaf_size_03(self):
        self.assertEqual(
            parse("""Leaf blades deltate to ± rhombic or ovate, 13–37 × 7–32 mm,"""),
            [
                Size(
                    start=43,
                    end=58,
                    dims=[
                        Dimension(
                            dim="length",
                            units="mm",
                            low=13,
                            high=37,
                            start=43,
                            end=48,
                        ),
                        Dimension(
                            dim="width",
                            units="mm",
                            low=7,
                            high=32,
                            start=51,
                            end=58,
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
