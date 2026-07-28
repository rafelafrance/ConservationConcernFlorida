#!/usr/bin/env python

import argparse
import csv
import json
import logging
import textwrap
import time
from pathlib import Path
from urllib.error import HTTPError

from playwright.sync_api import TimeoutError as PwTimeoutError
from playwright.sync_api import sync_playwright
from pylib import log

ERROR_RETRY = 2  # Make a few attempts to download a page
TIMEOUT = 2  # Wait this many seconds for the page to load

BASE_URL = "https://explorer.natureserve.org"


def main(args: argparse.Namespace) -> None:
    started = log.job_began(args=args)

    args.html_dir.mkdir(parents=True, exist_ok=True)

    nature_serve = get_nature_serve_taxa(args.nature_serve_json)
    logging.info(f"There are {len(nature_serve)} nature serve records.")

    targets = get_target_taxa(args.target_taxa_csv)
    logging.info(f"There are {len(targets)} target taxa.")

    targets = [t for t in targets if t in nature_serve]
    targets = targets[: args.limit]
    logging.info(f"There are {len(targets)} overlapping taxa.")

    for i, target in enumerate(targets, 1):
        print(i, target)
        record = nature_serve[target]
        path = get_download_file_name(record, args.html_dir)
        url = get_download_url(record)
        download(path, url)

    log.job_elapsed(started)


def download(path: Path, url: str, retries: int = ERROR_RETRY) -> None:
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
                page.goto(url, wait_until="networkidle")  # domcontentloaded

                with path.open("w", encoding="utf-8") as f:
                    f.write(page.content())

                browser.close()

            break

        except TimeoutError, HTTPError, PwTimeoutError:
            time.sleep(attempt * TIMEOUT)


def get_target_taxa(target_taxa_csv: Path) -> list[str]:
    with target_taxa_csv.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        targets = {r["Scientific.Name"] for r in reader}
    return sorted(targets)


def get_nature_serve_taxa(nature_serve_json: Path) -> dict[str, dict]:
    with nature_serve_json.open() as f:
        data = json.load(f)

    nature_serve = {}
    for item in data:
        nature_serve[item["scientificName"]] = item
        species_global = item.get("speciesGlobal", {})
        synonyms = species_global.get("synonyms", [])
        for syn in synonyms:
            syn = " ".join(syn.split())
            nature_serve[syn] = item

    return nature_serve


def get_download_file_name(nature_serve_rec: dict, parent: Path) -> Path:
    id_ = nature_serve_rec["elementGlobalId"]
    taxon = nature_serve_rec["scientificName"]
    taxon = taxon.replace(" ", "_")
    return parent / f"{taxon}_{id_}.html"


def get_download_url(nature_serve_rec: dict) -> str:
    return f"{BASE_URL}{nature_serve_rec['nsxUrl']}"


def parse_args() -> argparse.Namespace:
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

    arg_parser.add_argument(
        "--limit",
        type=int,
        metavar="INT",
        help="""Limit to this many downloads. Used for debugging.""",
    )

    args = arg_parser.parse_args()

    return args


if __name__ == "__main__":
    ARGS = parse_args()
    main(ARGS)
