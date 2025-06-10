import unittest

import ccf.pylib.fna_parse_treatment as fna


class TestFnaRuleParser(unittest.TestCase):
    def setUp(self):
        fna.SHAPES, fna.FRUIT_TYPES, fna.DURATION = fna.get_terms()

    def test_fna_rule_parser_01(self):
        """It only fills a record field once but scans all fields."""
        treatment = {"Culm": "10mm", "Annual": "evergreen 4mm"}
        record = {}
        fna.parse_treatment(record, treatment)
        self.assertEqual(
            record,
            {
                "deciduousness": "evergreen",
                "plant_height_min_cm": None,
                "plant_height_low_cm": 1.0,
                "plant_height_high_cm": None,
                "plant_height_max_cm": None,
            },
        )

    def test_fna_rule_parser_02(self):
        treatment = {
            "Plants": "perennial; rhizomatous,",
            "Culms": "20-250 cm tall, 3-10 mm thick,",
        }
        record = {}
        fna.parse_treatment(record, treatment)
        self.assertEqual(
            record,
            {
                "deciduousness": "",
                "plant_height_min_cm": None,
                "plant_height_low_cm": 20.0,
                "plant_height_high_cm": 250.0,
                "plant_height_max_cm": None,
            },
        )

    def test_fna_rule_parser_03(self):
        treatment = {
            "Plants": "perennial; cespitose. ",
            "Culms": "40-90 cm, erect, unbranched, glabrous; nodes 1-2. ",
        }
        record = {}
        fna.parse_treatment(record, treatment)
        self.assertEqual(
            record,
            {
                "deciduousness": "",
                "plant_height_min_cm": None,
                "plant_height_low_cm": 40.0,
                "plant_height_high_cm": 90.0,
                "plant_height_max_cm": None,
            },
        )

    def test_fna_rule_parser_04(self):
        treatment = {
            "Plants": "perennial.",
            "Culms": "1-1.5 m.",
        }
        record = {}
        fna.parse_treatment(record, treatment)
        self.assertEqual(
            record,
            {
                "deciduousness": "",
                "plant_height_min_cm": None,
                "plant_height_low_cm": 100.0,
                "plant_height_high_cm": 150.0,
                "plant_height_max_cm": None,
            },
        )

    def test_fna_rule_parser_05(self):
        treatment = {
            "Leaf": "-blade narrowly elliptic to narrowly obovate or oblanceolate, "
            "40-210 × 20-80 mm,",
        }
        record = {}
        fna.parse_treatment(record, treatment)
        self.assertEqual(
            record,
            {
                "leaf_length_min_cm": None,
                "leaf_length_low_cm": 4.0,
                "leaf_length_high_cm": 21.0,
                "leaf_length_max_cm": None,
                "leaf_width_min_cm": None,
                "leaf_width_low_cm": 2.0,
                "leaf_width_high_cm": 8.0,
                "leaf_width_max_cm": None,
                "leaf_thickness_min_cm": None,
                "leaf_thickness_low_cm": None,
                "leaf_thickness_high_cm": None,
                "leaf_thickness_max_cm": None,
                "leaf_shape": "elliptic | obovate | oblanceolate",
            },
        )

    def test_fna_rule_parser_06(self):
        treatment = {
            "Utricles": "elliptic or obovoid, 1.5–2.5 mm,",
        }
        record = {}
        fna.parse_treatment(record, treatment)
        self.assertEqual(
            record,
            {
                "fruit_type": "utricles",
                "fruit_length_min_cm": None,
                "fruit_length_low_cm": 0.15,
                "fruit_length_high_cm": 0.25,
                "fruit_length_max_cm": None,
                "fruit_width_min_cm": None,
                "fruit_width_low_cm": None,
                "fruit_width_high_cm": None,
                "fruit_width_max_cm": None,
                "fruit_diameter_min_cm": None,
                "fruit_diameter_low_cm": None,
                "fruit_diameter_high_cm": None,
                "fruit_diameter_max_cm": None,
            },
        )

    def test_fna_rule_parser_07(self):
        treatment = {
            "Acorns": "4.5-8 mm high × 10-18 mm wide",
        }
        record = {}
        fna.parse_treatment(record, treatment)
        self.assertEqual(
            record,
            {
                "fruit_type": "acorns",
                "fruit_length_min_cm": None,
                "fruit_length_low_cm": 0.45,
                "fruit_length_high_cm": 0.8,
                "fruit_length_max_cm": None,
                "fruit_width_min_cm": None,
                "fruit_width_low_cm": 1.0,
                "fruit_width_high_cm": 1.8,
                "fruit_width_max_cm": None,
                "fruit_diameter_min_cm": None,
                "fruit_diameter_low_cm": None,
                "fruit_diameter_high_cm": None,
                "fruit_diameter_max_cm": None,
            },
        )

    def test_fna_rule_parser_08(self):
        treatment = {
            "Drupes": "juicy, sweet, glossy black, 6–9 mm diam.,",
        }
        record = {}
        fna.parse_treatment(record, treatment)
        self.assertEqual(
            record,
            {
                "fruit_type": "drupes",
                "fruit_length_min_cm": None,
                "fruit_length_low_cm": None,
                "fruit_length_high_cm": None,
                "fruit_length_max_cm": None,
                "fruit_width_min_cm": None,
                "fruit_width_low_cm": None,
                "fruit_width_high_cm": None,
                "fruit_width_max_cm": None,
                "fruit_diameter_min_cm": None,
                "fruit_diameter_low_cm": 0.6,
                "fruit_diameter_high_cm": 0.9,
                "fruit_diameter_max_cm": None,
            },
        )
