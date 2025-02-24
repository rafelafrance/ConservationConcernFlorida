#!/usr/bin/env python

import argparse
import csv
import textwrap
import time
from pathlib import Path

from pylib import log
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://ser-sid.org"

LEN_SPECIES = 2


def main(args):
    log.started()

    targets = get_taxa(args.taxon_csv)

    args.html_dir.mkdir(parents=True, exist_ok=True)

    options = Options()
    options.add_argument("--headless=new")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )

    driver.get("https://httpbin.io/ip")
    print(driver.page_source)
    driver.quit()
    return

    for species in targets:
        path = args.html_dir / (species.replace(" ", "_") + ".html")
        if path.exists():
            print(f"{species} completed")
            continue

        driver.get(BASE_URL)
        get_seed_data(driver, species, path)
        break

    log.finished()


def get_seed_data(driver, species: str, path: Path):
    try:
        search = WebDriverWait(driver, 5).until(
            ec.presence_of_element_located(By.NAME, "input")
        )

        search.send_keys(species)

        WebDriverWait(driver, 5).until(
            ec.presence_of_element_located(By.TAG_NAME, "h4")
        )

        ul = driver.find_elements(By.CLASS_NAME, "italic")

        for li in ul:
            text = li.text
            parts = text.split()
            if len(parts) == LEN_SPECIES:
                li.click()
                WebDriverWait(driver, 10).until(
                    ec.presence_of_element_located(By.CLASS_NAME, "cursor-pointer")
                )

                with path.open("w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                    return

        path = path.with_stem(path.stem + "_not_found")
        path.open("a").close()

    except (NoSuchElementException, TimeoutException) as err:
        path = path.with_stem(path.stem + "_error")
        with path.open("w", encoding="utf-8") as f:
            f.write(err)


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
