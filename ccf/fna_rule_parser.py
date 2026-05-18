#!/usr/bin/env python3

import argparse
import re
import textwrap
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

from ccf.pylib import log, pipeline, str_util


def main(args: argparse.Namespace) -> None:
    log.started()

    pages = sorted(args.html_dir.glob("*.html"), key=lambda t: t.stem.split("_")[1:])

    with args.target_csv.open() as f:
        targets = {ln.strip() for ln in f.readlines()}

    pipe = pipeline.build()

    records = []

    hits, sects = 0, 0

    for page in tqdm(pages):
        with page.open() as f:
            text = f.read()
        name = " ".join(page.stem.split("_")[1:])
        if name not in targets:
            continue
        hits += 1
        print(f"Hit {name}")

        soup = BeautifulSoup(text, features="lxml")
        treatment = find_treatment(soup)

        section = treatment.get("Leaf", treatment.get("Leaves"))
        if not section:
            continue

        sects += 1
        print(section)

        doc = pipe(section)
        traits = [e._.trait for e in doc.ents]

        record = {"taxon": page.stem.replace("_", " ")}
        shape, surface, margin = [], [], []

        for trait in traits:
            print(trait)
            match trait._trait:
                case "shape":
                    shape.append(trait.shape)
                case "surface":
                    surface.append(trait.surface)
                case "margin":
                    margin.append(trait.margin)

        print()
        record["shape"] = ", ".join(shape)
        record["surface"] = ", ".join(surface)
        record["margin"] = ", ".join(margin)

        records.append(record)

    print(f"Hits {hits}  with leaf section {sects}")
    df = pd.DataFrame(records)
    df.to_csv(args.out_csv, index=False)

    log.finished()


def find_treatment(soup: BeautifulSoup) -> dict:
    treatment = soup.find("span", class_="statement")
    if not treatment:
        return {}

    text = str(treatment).replace("<i>", "").replace("</i>", "")
    text = re.sub(r"(Perennials|Annuals|Biennials);", r"<b>\1</b>", text)
    text = str_util.clean(text)

    soup2 = BeautifulSoup(text, features="lxml")
    parts = [p.text.strip() for p in soup2.find_all(string=True)]
    # print(f"{parts=}")
    treatment = dict(zip(parts[0::2], parts[1::2], strict=True))
    return treatment


def parse_args() -> argparse.Namespace:
    arg_parser = argparse.ArgumentParser(
        allow_abbrev=True,
        description=textwrap.dedent("Parse data from downloaded HTML files."),
    )
    arg_parser.add_argument(
        "--html-dir",
        type=Path,
        required=True,
        metavar="PATH",
        help="""Parse HTML files in this directory.""",
    )
    arg_parser.add_argument(
        "--target-csv",
        type=Path,
        required=True,
        metavar="PATH",
        help="""Only parse an HTML file if it is in this file.""",
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
    ARGS = parse_args()
    main(ARGS)
