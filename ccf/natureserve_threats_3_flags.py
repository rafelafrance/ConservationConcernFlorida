#!/usr/bin/env python

import argparse
import textwrap
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from ccf.pylib import log
from ccf.pylib import natureserve_threats as nt


def flag_threats(args: argparse.Namespace) -> None:
    log.started()

    in_data = pd.read_csv(args.in_csv, dtype=str)
    in_data = in_data.fillna("").to_dict("records")

    # Set simple word matching flags
    for row in in_data:
        words = " ".join(row["target"].lower().split())
        for key, value in nt.FLAGS.items():
            if key in words:
                row[value] = "1"

    df = pd.DataFrame(in_data)
    df.to_csv(args.out_csv, index=False)

    log.finished()


def parse_args() -> argparse.Namespace:
    arg_parser = argparse.ArgumentParser(
        description=textwrap.dedent(
            """Extract IUCN threat categories from NatureServe threat text."""
        ),
    )
    arg_parser.add_argument(
        "--in-csv",
        type=Path,
        required=True,
        metavar="PATH",
        help="""The CSV file containing the original threats.""",
    )
    arg_parser.add_argument(
        "--out-csv",
        type=Path,
        required=True,
        metavar="PATH",
        help="""Output threat categories to this CSV file.""",
    )
    args = arg_parser.parse_args()
    return args


if __name__ == "__main__":
    ARGS = parse_args()
    load_dotenv()
    flag_threats(ARGS)
