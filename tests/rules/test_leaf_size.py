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

    def test_leaf_size_05(self):
        self.assertEqual(
            parse(
                """
                Leaves opposite; filiform, 1–1.2(–2.8) mm,
                usually glabrous, rarely pilose; petiole 0.4–1 mm, usually glabrous;
                blade, 4.4–12 × 2.6–7.6 mm,
                """
            ),
            [
                Size(
                    start=119,
                    end=138,
                    dims=[
                        Dimension(
                            dim="length",
                            units="mm",
                            low=4.4,
                            high=12.0,
                            start=119,
                            end=125,
                        ),
                        Dimension(
                            dim="width",
                            units="mm",
                            low=2.6,
                            high=7.6,
                            start=128,
                            end=138,
                        ),
                    ],
                )
            ],
        )

    def test_leaf_size_06(self):
        self.assertEqual(
            parse(
                """
                Leaves: mostly cauline on proximal 2/3–7/8 of plant heights;
                petioles 0 or 10–35+ mm; blades usually 1(–2)-irregularly pinnately
                or ± pedately lobed with (3–)5–9+ lobes, rarely simple,
                simple blades or terminal lobes filiform,
                15–45(–90+) × (0.5–)2–8(–12+) mm.
                """
            ),
            [],
        )

    def test_leaf_size_07(self):
        self.assertEqual(
            parse("""broad petiole over 7 mm wide,"""),
            [],
        )

    def test_leaf_size_08(self):
        self.assertEqual(
            parse(
                """
                Leaves: stipules 9–15 mm; petiole to 1/2 as long as blade
                blade 3–5-lobed, 4–10 cm,
                """
            ),
            [
                Size(
                    start=75,
                    end=82,
                    dims=[
                        Dimension(
                            dim="length",
                            units="cm",
                            low=4,
                            high=10,
                            start=75,
                            end=82,
                        ),
                    ],
                )
            ],
        )

    def test_leaf_size_09(self):
        self.assertEqual(
            parse(
                """
                Leaf-blades pale to bright green, shorter to longer than culms,
                0.8–2.5 mm wide,
                """
            ),
            [
                Size(
                    start=64,
                    end=79,
                    dims=[
                        Dimension(
                            dim="width",
                            units="mm",
                            low=0.8,
                            high=2.5,
                            start=64,
                            end=79,
                        ),
                    ],
                )
            ],
        )
