#!/usr/bin/env python

import argparse
import random
import textwrap
import time
from pathlib import Path
from urllib.error import HTTPError

from playwright.sync_api import TimeoutError as PwTimeoutErrror
from playwright.sync_api import sync_playwright
from pylib import log, util

ERROR_RETRY = 5  # Make a few attempts to download a page
TIMEOUT = 10_000  # Wait this many msec for the page to load


def main():
    log.started()
    args = parse_args()

    args.html_dir.mkdir(parents=True, exist_ok=True)

    targets = util.get_target_taxa(args.target_taxa_csv)
    nature_serve = util.get_nature_serve_taxa(args.nature_serve_json)

    random.shuffle(targets)  # Silliness... I'm not fooling anyone

    for i, target in enumerate(targets, 1):
        print(i, target)
        if target not in nature_serve:
            continue
        record = nature_serve[target]
        path = util.get_download_file_name(record, args.html_dir)
        url = util.get_download_url(record)
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

        except (TimeoutError, HTTPError, PwTimeoutErrror):
            time.sleep(attempt * TIMEOUT)


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
