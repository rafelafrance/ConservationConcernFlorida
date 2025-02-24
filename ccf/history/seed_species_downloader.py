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

    targets = get_taxa(args.taxon_csv)
    urls = get_urls(args.url_csv)

    args.html_dir.mkdir(parents=True, exist_ok=True)

    driver = webdriver.Chrome()

    driver.implicitly_wait(5)
    driver.set_window_size(2252, 2148)

    for species in targets:
        if species not in urls:
            print(f"{species} missing")
            continue

        path = args.html_dir / (species.replace(" ", "_") + ".html")
        if path.exists():
            print(f"{species} completed")
            continue

        search(driver, species)

        # download_species(driver, url, path, species)

    log.finished()


def search(driver, species: str):
    try:
        driver.find_element(By.CSS_SELECTOR, ".text-md").click()
        time.sleep(1)

        driver.find_element(By.NAME, "input").send_keys(species)

        driver.find_element(By.TAG_NAME, "h4")

    except (NoSuchElementException, TimeoutException):
        return False

    return True


def download_species(driver, url, path: Path, species: str):
    try:
        driver.get(url)
        driver.find_element(By.CSS_SELECTOR, ".text-2xl")

        with path.open("w", encoding="utf-8") as f:
            f.write(driver.page_source)

        time.sleep(1)

        print(f"{species} succeded")

    except (NoSuchElementException, TimeoutException):
        print(f"{species} failed")

    finally:
        driver.quit()


def get_taxa(taxon_csv: Path) -> list[str]:
    with taxon_csv.open() as f:
        reader = csv.DictReader(f)
        taxa = {r["parentTaxon"] for r in reader}
    taxa = sorted(taxa)
    return taxa


def get_urls(url_csv: Path) -> dict[str, str]:
    with url_csv.open() as f:
        reader = csv.DictReader(f)
        urls = {u["taxon"]: u["href"] for u in reader}
    return urls


def parse_args():
    arg_parser = argparse.ArgumentParser(
        description=textwrap.dedent(
            """
        Download species data from the Seed Information Database website.
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
        "--url-csv",
        type=Path,
        required=True,
        help="""The CSV file containing URLs to seed data by species.""",
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
