import unittest

from ccf.pylib.dimension import Dimension
from ccf.rules.leaf_size import LeafSize
from ccf.rules.shape import Shape
from ccf.rules.size import Size
from tests.setup import parse


class TestLeafSize(unittest.TestCase):
    def test_leaf_size_00(self):
        parse(
            """
            leaves 3-foliolate, (7–)10–20(–30) cm,
            """
        )

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
                LeafSize(
                    start=0,
                    end=28,
                    part="leaf",
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
                Shape(start=17, end=25, shape="filiform"),
                Size(
                    start=27,
                    end=41,
                    dims=[
                        Dimension(
                            dim="length",
                            units="mm",
                            low=1.0,
                            high=1.2,
                            max=2.8,
                            start=27,
                            end=41,
                        )
                    ],
                ),
                LeafSize(
                    start=112,
                    end=138,
                    _trait="leaf_size",
                    part="leaf",
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
                ),
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
            [
                Shape(start=219, end=227, shape="filiform"),
                Size(
                    start=229,
                    end=262,
                    dims=[
                        Dimension(
                            dim="length",
                            units="mm",
                            low=15.0,
                            high=45.0,
                            max=90.0,
                            start=229,
                            end=240,
                        ),
                        Dimension(
                            dim="width",
                            units="mm",
                            min=0.5,
                            low=2.0,
                            high=8.0,
                            max=12.0,
                            start=243,
                            end=262,
                        ),
                    ],
                ),
            ],
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

    def test_leaf_size_10(self):
        self.assertEqual(
            parse("""air spaces shorter than 0.3 mm;"""),
            [],
        )

    def test_leaf_size_11(self):
        self.assertEqual(
            parse("""hairs to 4 mm;"""),
            [],
        )

    def test_leaf_size_12(self):
        self.assertEqual(
            parse("""stipules 2–5 stipitate glands, to 0.5 mm;"""),
            [],
        )

    def test_leaf_size_13(self):
        self.assertEqual(
            parse("""stipules persistent, subulate, 1–2 × 0.5–1 mm,"""),
            [Shape(start=21, end=29, shape="subulate")],
        )

    def test_leaf_size_14(self):
        self.assertEqual(
            parse("""peti­ole 1–4 cm;"""),
            [],
        )

    def test_leaf_size_15(self):
        self.assertEqual(
            parse("""long-petiolate (to 15 cm;"""),
            [],
        )

    def test_leaf_size_16(self):
        self.assertEqual(
            parse("""blades 2-45 cm long, 0.3-1.5(2) mm wide,"""),
            [
                LeafSize(
                    start=0,
                    end=39,
                    part="leaf",
                    dims=[
                        Dimension(
                            dim="length",
                            units="cm",
                            low=2.0,
                            high=45.0,
                            start=7,
                            end=19,
                        ),
                        Dimension(
                            dim="width",
                            units="mm",
                            low=0.3,
                            high=1.5,
                            max=2.0,
                            start=21,
                            end=39,
                        ),
                    ],
                )
            ],
        )

    def test_leaf_size_17(self):
        self.assertEqual(
            parse("""blades 10-25 cm long, 15-30 mm wide,"""),
            [
                LeafSize(
                    start=0,
                    end=35,
                    part="leaf",
                    dims=[
                        Dimension(
                            dim="length",
                            units="cm",
                            low=10.0,
                            high=25.0,
                            start=7,
                            end=20,
                        ),
                        Dimension(
                            dim="width",
                            units="mm",
                            low=15.0,
                            high=30.0,
                            start=22,
                            end=35,
                        ),
                    ],
                )
            ],
        )

    def test_leaf_size_18(self):
        self.assertEqual(
            parse("""1.5–3.5(–4.5) cm ×5–12 mm,"""),
            [
                Size(
                    start=0,
                    end=25,
                    dims=[
                        Dimension(
                            dim="length",
                            units="cm",
                            low=1.5,
                            high=3.5,
                            max=4.5,
                            start=0,
                            end=16,
                        ),
                        Dimension(
                            dim="width",
                            units="mm",
                            low=5.0,
                            high=12.0,
                            start=18,
                            end=25,
                        ),
                    ],
                )
            ],
        )

    def test_leaf_size_19(self):
        self.assertEqual(
            parse("""1–2 mm margin"""),
            [],
        )

    def test_leaf_size_20(self):
        self.assertEqual(
            parse("""stipules linear-lanceolate, 2–6 mm,"""),
            [
                Shape(start=9, end=15, shape="linear"),
                Shape(start=16, end=26, shape="lanceolate"),
            ],
        )

    def test_leaf_size_21(self):
        self.assertEqual(
            parse("""connate at base, filiform, 1–1.2(–2.8) mm,"""),
            [
                Shape(start=17, end=25, shape="filiform"),
            ],
        )

    def test_leaf_size_22(self):
        self.assertEqual(
            parse("""ciliate, 0.2–0.3 mm,"""),
            [],
        )
