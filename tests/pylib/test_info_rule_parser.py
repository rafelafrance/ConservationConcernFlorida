import unittest

from bs4 import BeautifulSoup

import ccf.pylib.fna_parse_treatment as fna


class TestInfoParser(unittest.TestCase):
    def test_fna_info_parser_01(self):
        text = """
        <div class="treatment-info">
        <br/>
        Phenology: Flowering summer–fall.
        <br/>
        Habitat: Gravel, sand bars, sidewalks
        <br/>
        Elevation: 0–800\xa0m.
        </div>
        """
        soup = BeautifulSoup(text, features="lxml")
        info = fna.get_info(soup)
        record = {}

        fna.parse_info(info, record)
        self.assertEqual(
            record,
            {
                "flowering_time": "Flowering summer-fall.",
                "habitat": "Gravel, sand bars, sidewalks",
                "elevation_min_m": 0.0,
                "elevation_max_m": 800.0,
            },
        )
