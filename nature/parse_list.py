#!/usr/bin/env python3
import argparse
import textwrap
from pathlib import Path

from pylib import util


def main():
    args = parse_args()

    targets = util.get_target_taxa(args.target_taxa_csv)
    nature_serve = util.get_nature_serve_taxa(args.nature_serve_json)

    for target in targets:
        if target not in nature_serve:
            continue
        print(target)


def parse_args():
    arg_parser = argparse.ArgumentParser(
        allow_abbrev=True,
        description=textwrap.dedent("Parse data from downloaded JSON files."),
    )

    arg_parser.add_argument(
        "--target-taxa-csv",
        type=Path,
        required=True,
        metavar="PATH",
        help="""The CSV file containing the target taxa.""",
    )

    arg_parser.add_argument(
        "--nature-serve-json",
        type=Path,
        required=True,
        metavar="PATH",
        help="""Parse the data in this downloaded NatureServe JSON list page.""",
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
    main()
