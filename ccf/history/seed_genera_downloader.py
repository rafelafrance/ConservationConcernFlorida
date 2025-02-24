#!/usr/bin/env python

import argparse
import csv
import textwrap
import time
from pathlib import Path

from pylib import log
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By

BASE_URL = "https://ser-sid.org"


def main(args):
    log.started()

    taxa = get_taxa(args.taxon_csv)

    args.html_dir.mkdir(parents=True, exist_ok=True)

    driver = webdriver.Chrome()

    driver.implicitly_wait(5)
    driver.set_window_size(2252, 2148)

    driver.get(BASE_URL)

    genera = {t.split()[0] for t in taxa}
    genera = sorted(genera)

    for genus in genera:
        path = args.html_dir / (genus + ".html")
        if path.exists():
            print(f"{genus} skipped")
            continue

        download_genus(driver, path, genus)

    log.finished()


def download_genus(driver, path: Path, genus: str):
    try:
        driver.find_element(By.CSS_SELECTOR, ".text-md").click()
        time.sleep(1)

        driver.find_element(By.NAME, "input").click()
        driver.find_element(By.NAME, "input").send_keys(genus)

        driver.find_element(By.TAG_NAME, "h4")

        with path.open("w", encoding="utf-8") as f:
            f.write(driver.page_source)

        time.sleep(1)

        driver.find_element(By.CSS_SELECTOR, ".text-md").click()
        time.sleep(2)

        print(f"{genus} succeded")

    except (NoSuchElementException, TimeoutException):
        print(f"{genus} failed")


def get_taxa(taxon_csv: Path) -> list[str]:
    with taxon_csv.open() as f:
        reader = csv.DictReader(f)
        taxa = {r["parentTaxon"] for r in reader}
    taxa = sorted(taxa)
    return taxa


def parse_args():
    arg_parser = argparse.ArgumentParser(
        description=textwrap.dedent(
            """
        Download data from the Seed Information Database website.
        """
        ),
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

    args = arg_parser.parse_args()

    return args


if __name__ == "__main__":
    ARGS = parse_args()
    main(ARGS)
