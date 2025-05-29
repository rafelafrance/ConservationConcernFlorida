#!/usr/bin/env python3

import argparse
import re
import textwrap
from collections import defaultdict
from pathlib import Path

import ftfy
from bs4 import BeautifulSoup
from fna_rule_parser import PARSE


def main(args):
    pages = sorted(args.html_dir.glob("*.html"))

    all_keys = defaultdict(list)
    all_pages = defaultdict(list)

    for page in pages:
        print(page.stem)
        with page.open() as f:
            text = f.read()

        soup = BeautifulSoup(text, features="lxml")

        treat = get_treatment(soup)

        for key, value in treat.items():
            all_keys[key].append(value)
            all_pages[key].append(page.stem)

    missing_keys = {k: v for k, v in all_keys.items() if k not in PARSE}
    missing_keys = dict(sorted(missing_keys.items()))

    print()
    for key, taxon in missing_keys.items():
        print(f"{key:<12} {taxon[:]}")
        print(f"{'':<12} {all_pages[key][:3]}")
        print()
    print()
    for key in missing_keys:
        print(f'"{key}": None,')
    print()
    print(f"All keys {len(all_keys)}, missing keys {len(missing_keys)}")


def get_treatment(soup):
    treat = soup.find("span", class_="statement")
    if not treat:
        return {}

    text = str(treat).replace("<i>", "").replace("</i>", "")
    text = re.sub(r"(Perennials|Annuals|Biennials);", r"<b>\1</b>", text)
    text = clean(text)

    soup2 = BeautifulSoup(text, features="lxml")
    parts = [p.text.strip() for p in soup2.find_all(string=True)]
    treat = dict(zip(parts[0::2], parts[1::2], strict=True))
    return treat


def clean(text):
    text = ftfy.fix_text(text)  # Handle common mojibake
    text = re.sub(r"[–—\-]+", "-", text)
    text = text.replace("±", "+/-")
    return text


def parse_args():
    arg_parser = argparse.ArgumentParser(
        allow_abbrev=True,
        description=textwrap.dedent(
            "Get keys from treatments in downloaded HTML files."
        ),
    )

    arg_parser.add_argument(
        "--html-dir",
        type=Path,
        required=True,
        metavar="PATH",
        help="""Parse HTML files in this directory.""",
    )

    args = arg_parser.parse_args()

    return args


if __name__ == "__main__":
    ARGS = parse_args()
    main(ARGS)
