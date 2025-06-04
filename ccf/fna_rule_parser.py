#!/usr/bin/env python3

import argparse
import textwrap
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

import ccf.pylib.fna_parse_treatment as fna
from ccf.pylib import log


def main(args):
    log.started()

    pages = sorted(args.html_dir.glob("*.html"))

    fna.SHAPES, fna.FRUIT_TYPES, fna.DURATION = fna.get_terms()

    records = []

    for page in tqdm(pages):
        # print(page.stem)
        with page.open() as f:
            text = f.read()

        soup = BeautifulSoup(text, features="lxml")

        treatment = fna.find_treatment(soup)
        record = fna.init_record(page)
        fna.parse_treatment(record, treatment)

        info = fna.get_info(soup)
        if info:
            fna.parse_info(info, record)

        records.append(record)

    pd.DataFrame(records).to_csv(args.out_csv, index=False)

    log.finished()


def parse_args():
    arg_parser = argparse.ArgumentParser(
        allow_abbrev=True,
        description=textwrap.dedent("Parse data from downloaded HTML files."),
    )

    arg_parser.add_argument(
        "--html-dir",
        type=Path,
        required=True,
        metavar="PATH",
        help="""Parse HTML files in this directory.""",
    )

    arg_parser.add_argument(
        "--out-csv",
        type=Path,
        metavar="PATH",
        help="""Output the results to this CSV file.""",
    )

    args = arg_parser.parse_args()

    return args


if __name__ == "__main__":
    ARGS = parse_args()
    main(ARGS)
