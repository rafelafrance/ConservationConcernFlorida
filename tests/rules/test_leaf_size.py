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
                    units="cm",
                    dims=[
                        Dimension(
                            dim="length",
                            units="mm",
                            min=0.5,
                            low=1.0,
                            high=3.0,
                            max=5.0,
                        )
                    ],
                ),
                Size(
                    start=63,
                    end=87,
                    units="cm",
                    dims=[
                        Dimension(
                            dim="length",
                            units="cm",
                            min=None,
                            low=4.0,
                            high=11.0,
                            max=13.0,
                        ),
                        Dimension(
                            dim="width",
                            units="cm",
                            min=None,
                            low=2.5,
                            high=8.0,
                            max=9.0,
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
                    units="cm",
                    dims=[
                        Dimension(
                            dim="length",
                            units="cm",
                            min=None,
                            low=12.0,
                            high=18.0,
                            max=None,
                        )
                    ],
                ),
                LeafSize(
                    start=70,
                    end=85,
                    part="midrib",
                    units="cm",
                    dims=[
                        Dimension(
                            dim="length",
                            units="cm",
                            min=None,
                            low=2.0,
                            high=4.0,
                            max=None,
                        )
                    ],
                ),
                Size(
                    start=122,
                    end=130,
                    units="cm",
                    dims=[
                        Dimension(
                            dim="length",
                            units="cm",
                            min=None,
                            low=15.0,
                            high=37.0,
                            max=None,
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
                    units="cm",
                    dims=[
                        Dimension(
                            dim="length",
                            units="mm",
                            min=None,
                            low=1.3,
                            high=3.7,
                            max=None,
                        ),
                        Dimension(
                            dim="width",
                            units="mm",
                            min=None,
                            low=0.7,
                            high=3.2,
                            max=None,
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
                    units="cm",
                    dims=[
                        Dimension(
                            dim="length",
                            units="mm",
                            min=None,
                            low=1.3,
                            high=3.7,
                            max=None,
                        ),
                        Dimension(
                            dim="width",
                            units="mm",
                            min=None,
                            low=0.7,
                            high=3.2,
                            max=None,
                        ),
                    ],
                )
            ],
        )
