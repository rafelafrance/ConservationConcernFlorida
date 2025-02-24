#!/usr/bin/env python

import argparse
import csv
import textwrap
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from pylib import log
from tqdm import tqdm


def main(args):
    log.started()

    taxa = get_taxa(args.taxon_csv)

    pages = sorted(args.html_dir.glob("*.html"))

    records = []

    for page in tqdm(pages):
        with page.open() as f:
            page = f.read()

        soup = BeautifulSoup(page, features="lxml")

        for a in soup.find_all("a"):
            if a["href"].startswith("/species/"):
                div = a.find_all("div", {"class": "italic"})
                if div:
                    records.append({"taxon": div[0].text.strip(), "href": a["href"]})

    df = pd.DataFrame(records)
    df.to_csv(args.links_csv, index=False)

    in_records = {r["taxon"].split()[0] for r in records}
    file_names = {p.stem for p in pages}
    genera = {t.split()[0] for t in taxa}

    missing = genera - in_records
    print(f"{len(in_records)} {len(file_names)} {len(genera)} {len(missing)}")

    log.finished()


def get_taxa(taxon_csv: Path) -> list[str]:
    with taxon_csv.open() as f:
        reader = csv.DictReader(f)
        taxa = {r["parentTaxon"] for r in reader}
    taxa = sorted(taxa)
    return taxa


def parse_args():
    arg_parser = argparse.ArgumentParser(
        description=textwrap.dedent("""Fix downloaded see genera pages."""),
    )

    arg_parser.add_argument(
        "--taxon-csv",
        type=Path,
        required=True,
        help="""The CSV file containing the target taxa.""",
    )

    arg_parser.add_argument(
        "--html-dir",
        type=Path,
        required=True,
        help="""Save downloaded web pages into this directory.""",
    )

    arg_parser.add_argument(
        "--links-csv",
        type=Path,
        help="""Taxon names and links to this CSV.""",
    )

    args = arg_parser.parse_args()

    return args


if __name__ == "__main__":
    ARGS = parse_args()
    main(ARGS)
