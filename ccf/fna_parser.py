#!/usr/bin/env python3

import argparse
import csv
import re
import textwrap
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from pylib import log, pipeline
from pylib.rules.size import Dimension

PIPELINE = pipeline.build()


def main(args):  # noqa: PLR0915
    log.started()

    pages = sorted(args.html_dir.glob("*.html"))

    shapes, fruit_types, duration = get_terms()

    records = []

    for page in pages:
        print(page.stem)

        with page.open() as f:
            text = f.read()

        soup = BeautifulSoup(text, features="lxml")

        treat = get_treatment(soup)

        taxon = page.stem.replace("_", " ")
        taxon = taxon[0].upper() + taxon[1:]
        rec = {"taxon": taxon}

        length = plant_height(treat)
        rec["plant_height_min_cm"] = length.min
        rec["plant_height_low_cm"] = length.low
        rec["plant_height_high_cm"] = length.high
        rec["plant_height_max_cm"] = length.max

        rec["leaf_shape"] = leaf_shape(shapes, treat)

        length, width, thickness = leaf_size(treat)
        rec["leaf_length_min_cm"] = length.min
        rec["leaf_length_low_cm"] = length.low
        rec["leaf_length_high_cm"] = length.high
        rec["leaf_length_max_cm"] = length.max
        rec["leaf_width_min_cm"] = width.min
        rec["leaf_width_low_cm"] = width.low
        rec["leaf_width_high_cm"] = width.high
        rec["leaf_width_max_cm"] = width.max
        rec["leaf_thickness_min_cm"] = thickness.min
        rec["leaf_thickness_low_cm"] = thickness.low
        rec["leaf_thickness_high_cm"] = thickness.high
        rec["leaf_thickness_max_cm"] = thickness.max

        length, width = seed_size(treat)
        rec["seed_length_min_cm"] = length.min
        rec["seed_length_low_cm"] = length.low
        rec["seed_length_high_cm"] = length.high
        rec["seed_length_max_cm"] = length.max
        rec["seed_width_min_cm"] = width.min
        rec["seed_width_low_cm"] = width.low
        rec["seed_width_high_cm"] = width.high
        rec["seed_width_max_cm"] = width.max

        length, width = fruit_size(treat)
        rec["fruit_length_min_cm"] = length.min
        rec["fruit_length_low_cm"] = length.low
        rec["fruit_length_high_cm"] = length.high
        rec["fruit_length_max_cm"] = length.max
        rec["fruit_width_min_cm"] = width.min
        rec["fruit_width_low_cm"] = width.low
        rec["fruit_width_high_cm"] = width.high
        rec["fruit_width_max_cm"] = width.max

        rec["fruit_type"] = fruit_type(fruit_types, treat)

        rec["deciduousness"] = deciduousness(duration, treat)

        info = get_info(soup)

        rec["flowering_time"] = flowering_time(info)

        rec["habitat"] = habitat(info)

        elev = elevation(info)
        rec["elevation_min_m"] = elev.low / 100.0 if elev.low is not None else None
        rec["elevation_max_m"] = elev.high / 100.0 if elev.high is not None else None

        records.append(rec)

    pd.DataFrame(records).to_csv(args.out_csv, index=False)

    log.finished()


def get_treatment(soup):
    treat = soup.find("span", class_="statement")
    if not treat:
        return {}

    text = str(treat).replace("<i>", "").replace("</i>", "")

    soup2 = BeautifulSoup(text, features="lxml")
    parts = soup2.find_all(string=True)
    treat = {
        k.strip().lower(): v.strip().lower()
        for k, v in zip(parts[0::2], parts[1::2], strict=True)
    }
    return treat


def get_info(soup):
    info = soup.find("div", class_="treatment-info").find_all(string=True)
    info = [x for i in info if (x := i.strip().lower()) and i.find(":") > -1]
    info = {i.split(":")[0].strip(): i.split(":")[1].strip() for i in info}
    return info


def get_ent(text: str) -> Dimension:
    doc = PIPELINE(text)
    ent = next((e._.trait for e in doc.ents if e.label_ == "size"), None)
    return ent


def get_size(ent, dim: str = "length") -> Dimension:
    if not ent:
        return Dimension()
    dim_ = next((d for d in ent.dims if d.dim == dim), Dimension())
    return dim_


def plant_height(treat):
    text = treat.get("plants", "")
    ent = get_ent(text)
    length = get_size(ent, "length")
    return length


def leaf_shape(shapes, treat):
    words = [w for w in re.split(r"\W+", treat.get("leaf", "")) if w]
    shape = [w for w in words if w in shapes]
    return " | ".join(shape)


def leaf_size(treat):
    text = treat.get("leaf", "")
    ent = get_ent(text)
    length = get_size(ent, "length")
    width = get_size(ent, "width")
    thick = get_size(ent, "thickness")
    return length, width, thick


def seed_size(treat):
    text = treat.get("seeds", "")
    ent = get_ent(text)
    length = get_size(ent, "length")
    width = get_size(ent, "width")
    return length, width


def fruit_size(treat):
    text = treat.get("fruits", "")
    ent = get_ent(text)
    length = get_size(ent, "length")
    width = get_size(ent, "width")
    return length, width


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
    text = info.get("elevation", "")
    ent = get_ent(text)
    elev = get_size(ent, "length")
    return elev


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
