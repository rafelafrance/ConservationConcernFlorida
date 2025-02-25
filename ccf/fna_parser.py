#!/usr/bin/env python3

import argparse
import csv
import re
import textwrap
from pathlib import Path
from pprint import pp

from bs4 import BeautifulSoup
from pylib import log
from tqdm import tqdm


def main(args):
    log.started()

    pages = sorted(args.html_dir.glob("*.html"))

    shapes, fruit_types, duration = get_terms()

    records = []

    for page in tqdm(pages):
        with page.open() as f:
            page = f.read()

        soup = BeautifulSoup(page, features="lxml")

        rec = {}

        treat = soup.find("span", class_="statement").find_all(string=True)
        treat = {
            k.strip().lower(): v.strip().lower()
            for k, v in zip(treat[0::2], treat[1::2], strict=True)
        }
        pp(treat)

        rec["plant_height_max"] = plant_height_max(treat)
        rec["leaf_shape"] = leaf_shape(shapes, treat)
        rec["leaf_length"], rec["leaf_width"], rec["leaf_thickness"] = leaf_size(treat)
        # rec["seed_length"], rec["seed_width"] = seed_size(treat)
        rec["fruit_length"], rec["fruit_width"] = fruit_size(treat)
        rec["fruit_type"] = fruit_type(fruit_types, treat)
        rec["deciduousness"] = deciduousness(duration, treat)

        info = soup.find("div", class_="treatment-info").find_all(string=True)
        info = [x for i in info if (x := i.strip().lower())][:3]
        info = {i.split(":")[0].strip(): i.split(":")[1].strip() for i in info}

        rec["flowering_time"] = flowering_time(info)
        rec["habitat"] = habitat(info)
        rec["elevation_min"], rec["elevation_max"] = elevation(info)

        records.append(rec)
        pp(rec)
        break

    # pd.DataFrame(records).to_csv(args.out_csv, index=False)

    log.finished()


def plant_height_max(treat):
    plant = treat.get("plants", "")
    heights = re.findall(r"\d+\.?\d*", plant)
    max_ = max(float(h) for h in heights) if heights else None
    return max_


def leaf_shape(shapes, treat):
    words = [w for w in re.split(r"\W+", treat.get("leaf", "")) if w]
    shape = [w for w in words if w in shapes]
    return " | ".join(shape)


def leaf_size(treat):
    leaf = treat.get("leaf", "")
    print(leaf)
    return None, None, None


def seed_size(treat):
    seeds = treat.get("seeds", "")
    print(seeds)
    return None, None


def fruit_size(treat):
    fruit = treat.get("fruits", "")
    print(fruit)
    return None, None


def fruit_type(fruit_types, treat):
    words = [w for w in re.split(r"\W+", treat.get("fruits", "")) if w]
    types = [w for w in words if w in fruit_types]
    return " | ".join(types)


def deciduousness(duration, treat):
    words = [w for w in re.split(r"\W+", treat.get("plants", "")) if w]
    types = [w for w in words if w in duration]
    return " | ".join(types)


def flowering_time(info):
    return info.get("phenology", "")


def habitat(info):
    return info.get("habitat", "")


def elevation(info):
    elev = info.get("elevation", "")
    print(elev)
    return None, None


def get_terms():
    shape_file = Path(__file__).parent / "pylib" / "rules" / "terms" / "shapes.csv"
    fruit_file = Path(__file__).parent / "pylib" / "rules" / "terms" / "fruit_types.csv"
    dur_file = Path(__file__).parent / "pylib" / "rules" / "terms" / "leaf_duration.csv"

    with shape_file.open() as f:
        shapes = {r["pattern"] for r in csv.DictReader(f)}

    with fruit_file.open() as f:
        fruit_types = {r["pattern"] for r in csv.DictReader(f)}

    with dur_file.open() as f:
        duration = {r["pattern"] for r in csv.DictReader(f)}

    return shapes, fruit_types, duration


def parse_args():
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
        "--out-csv",
        type=Path,
        required=True,
        metavar="PATH",
        help="""Output the results to this CSV file.""",
    )

    args = arg_parser.parse_args()

    return args


if __name__ == "__main__":
    ARGS = parse_args()
    main(ARGS)
