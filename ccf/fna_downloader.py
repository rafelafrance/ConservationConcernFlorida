#!/usr/bin/env python

import argparse
import csv
import textwrap
import time
from pathlib import Path
from urllib.error import HTTPError

from playwright.sync_api import TimeoutError as PwTimeoutError
from playwright.sync_api import sync_playwright
from pylib import log

ERROR_RETRY = 2  # Make a few attempts to download a page
TIMEOUT = 2  # Wait this many seconds for the page to load

BASE_URL = "http://floranorthamerica.org"

# QUERY = """
#     [[Taxon family::Asteraceae]][[Taxon rank::species]][[Distribution::Fla.]]
#     """


def main(args):
    log.started()

    args.html_dir.mkdir(parents=True, exist_ok=True)

    taxa = get_target_taxa(args.taxon_csv)

    for i, taxon in enumerate(taxa, 1):
        print(i, taxon)
        name = taxon.replace(" ", "_")
        url = BASE_URL + f"/{name}"
        path = args.html_dir / f"{name}.html"
        download(path, url)

    log.finished()


def download(path: Path, url: str, retries: int = ERROR_RETRY):
    if path.exists():
        return

    for attempt in range(1, retries + 1):
        if attempt > 1:
            print(f"Attempt {attempt}")

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
                page = ctx.new_page()
                page.goto(url, wait_until="domcontentloaded")

                with path.open("w", encoding="utf-8") as f:
                    f.write(page.content())

                time.sleep(TIMEOUT)

                browser.close()

            break

        except (TimeoutError, HTTPError, PwTimeoutError):
            time.sleep(attempt * TIMEOUT)


def get_target_taxa(target_taxa_csv: Path) -> list[str]:
    with target_taxa_csv.open() as f:
        reader = csv.DictReader(f)
        targets = {r["parentTaxon"] for r in reader}
    return sorted(targets)


def parse_args():
    arg_parser = argparse.ArgumentParser(
        description=textwrap.dedent("""Download data from the NatureServe website."""),
    )

    arg_parser.add_argument(
        "--taxon-csv",
        type=Path,
        required=True,
        metavar="PATH",
        help="""The CSV file containing the target taxa.""",
    )

    arg_parser.add_argument(
        "--html-dir",
        type=Path,
        required=True,
        metavar="PATH",
        help="""Save downloaded web pages into this directory.""",
    )

    args = arg_parser.parse_args()

    return args


if __name__ == "__main__":
    ARGS = parse_args()
    main(ARGS)
