#!/usr/bin/env python3
import argparse
import textwrap
from pathlib import Path

from bs4 import BeautifulSoup


def main():
    args = parse_args()

    for web in args.in_html.glob("*.html"):
        print(web)
        with web.open() as f:
            page = f.read()

        soup = BeautifulSoup(page, features="lxml")

        for sect in soup.find_all("div", attrs={"class": "data-section"}):
            for div in sect.find_all("div"):
                if div.has_attr("class") and "status-display" in div.attrs["class"]:
                    for status in div.find_all("div"):
                        print(status)
                else:
                    print(div.text)
            print()


def parse_args():
    arg_parser = argparse.ArgumentParser(
        allow_abbrev=True,
        description=textwrap.dedent("Parse data from downloaded HTML files."),
    )

    arg_parser.add_argument(
        "--in-html",
        type=Path,
        required=True,
        metavar="PATH",
        help="""Parse HTML files in this directory.""",
    )

    arg_parser.add_argument(
        "--out-html",
        type=Path,
        metavar="PATH",
        help="""Output the results to this HTML file.""",
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
