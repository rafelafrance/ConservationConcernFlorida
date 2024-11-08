#!/usr/bin/env python

import argparse
import csv
import json
import random
import textwrap
import time
from pathlib import Path
from pprint import pp
from urllib.error import HTTPError

from playwright.sync_api import TimeoutError as PwTimeoutError
from playwright.sync_api import sync_playwright
from pylib import log

ERROR_RETRY = 5  # Make a few attempts to download a page
TIMEOUT = 15_000  # Wait this many milliseconds for the page to load

BASE_URL = "https://explorer.natureserve.org"


def main():
    log.started()
    args = parse_args()

    args.html_dir.mkdir(parents=True, exist_ok=True)

    targets = get_target_taxa(args.target_taxa_csv)
    nature_serve = get_nature_serve_taxa(args.nature_serve_json)

    random.shuffle(targets)  # Silliness... I'm not fooling anyone

    for i, target in enumerate(targets, 1):
        print(i, target)
        if target not in nature_serve:
            continue
        record = nature_serve[target]
        path = get_download_file_name(record, args.html_dir)
        url = get_download_url(record)
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
                page.goto(url)
                page.wait_for_timeout(TIMEOUT)

                with path.open("w", encoding="utf-8") as f:
                    f.write(page.content())

                browser.close()

            break

        except (TimeoutError, HTTPError, PwTimeoutError):
            time.sleep(attempt * TIMEOUT)


def get_target_taxa(target_taxa_csv: Path) -> list[str]:
    with target_taxa_csv.open() as f:
        reader = csv.DictReader(f)
        targets = {r["parentTaxon"] for r in reader}
    return sorted(targets)


def get_nature_serve_taxa(nature_serve_json: Path) -> dict[str, dict]:
    """Get a dict of nature serve taxa/synonyms and nature_serve records."""
    with nature_serve_json.open() as f:
        data = json.load(f)

    nature_serve = {}
    for item in data:
        nature_serve[item["scientificName"]] = item
        species_global = item.get("speciesGlobal", {})
        synomnyms = species_global.get("synonyms", [])
        for syn in synomnyms:
            syn = " ".join(syn.split()[:2])
            nature_serve[syn] = item

    return nature_serve


def get_download_file_name(nature_serve_rec: dict, parent: Path) -> Path:
    id_ = nature_serve_rec["elementGlobalId"]
    taxon = nature_serve_rec["scientificName"]
    taxon = taxon.replace(" ", "_")
    return parent / f"{taxon}_{id_}.html"


def get_download_url(nature_serve_rec: dict) -> str:
    return f"{BASE_URL}{nature_serve_rec['nsxUrl']}"


def compare_targets_and_nature_serve(
    targets: list[str], nature_serve: dict[str, dict]
) -> None:
    hits = 0
    misses = []
    for target in targets:
        hits += 1 if target in nature_serve else 0
        if target not in nature_serve:
            misses.append(target)

    print(f"Nature  {len(nature_serve)}")
    print(f"targets {len(targets)}")
    print(f"hits    {hits}")

    pp(sorted(misses))


def parse_args():
    arg_parser = argparse.ArgumentParser(
        description=textwrap.dedent("""Download data from the NatureServe website."""),
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
        "--html-dir",
        type=Path,
        required=True,
        metavar="PATH",
        help="""Save downloaded web pages into this directory.""",
    )

    args = arg_parser.parse_args()

    return args


if __name__ == "__main__":
    main()
