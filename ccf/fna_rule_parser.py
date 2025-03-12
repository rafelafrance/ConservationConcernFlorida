#!/usr/bin/env python3

import argparse
import csv
import re
import textwrap
from collections import defaultdict
from pathlib import Path

import ftfy
import pandas as pd
from bs4 import BeautifulSoup
from pylib import log, pipeline
from rules.size import Dimension

PIPELINE = pipeline.build()


SHAPES = set()
FRUIT_TYPES = set()
DURATION = set()


def main(args):
    global SHAPES, FRUIT_TYPES, DURATION

    log.started()

    pages = sorted(args.html_dir.glob("*.html"))

    SHAPES, FRUIT_TYPES, DURATION = get_terms()

    records = []

    all_keys = defaultdict(list)

    for page in pages:
        print(page.stem)

        with page.open() as f:
            text = f.read()

        soup = BeautifulSoup(text, features="lxml")

        treat = get_treatment(soup)

        if args.print_keys:
            for key, value in treat.items():
                all_keys[key].append(value)
            continue

        taxon = page.stem.replace("_", " ")
        taxon = taxon[0].upper() + taxon[1:]
        rec = {"taxon": clean(taxon).replace("×", "x ")}

        used = set()

        for key, text in treat.items():
            if (func := PARSE.get(key)) and func not in used:
                used.add(func)  # Only use a parse function once
                func(key, text, rec)

        info = get_info(soup)
        phenology(info, rec)
        habitat(info, rec)
        elevation(info, rec)

        records.append(rec)

    if args.print_keys:
        print()
        for key, taxon in dict(sorted(all_keys.items())).items():
            # print(f'"{key}": None,')
            print(f"{key:<12} {taxon[:4]}")
            print()
        print()

    else:
        pd.DataFrame(records).to_csv(args.out_csv, index=False)

    log.finished()


def get_treatment(soup):
    treat = soup.find("span", class_="statement")
    if not treat:
        return {}

    text = str(treat).replace("<i>", "").replace("</i>", "")
    text = clean(text)

    soup2 = BeautifulSoup(text, features="lxml")
    parts = [p.text.strip() for p in soup2.find_all(string=True)]
    treat = dict(zip(parts[0::2], parts[1::2], strict=True))
    return treat


def get_info(soup):
    info = soup.find("div", class_="treatment-info").find_all(string=True)
    info = [clean(x) for i in info if (x := i.strip()) and i.find(":") > -1]
    info = {i.split(":")[0].strip(): i.split(":")[1].strip() for i in info}
    return info


def clean(text):
    text = ftfy.fix_text(text)  # Handle common mojibake
    text = re.sub(r"[\-\–\—\—\–]+", "-", text)
    text = text.replace("±", "+/-")
    return text


def get_ent(text: str) -> Dimension | None:
    doc = PIPELINE(text)
    ent = next((e._.trait for e in doc.ents if e.label_ == "size"), None)
    return ent


def get_leaf_size_ent(text: str) -> Dimension | None:
    doc = PIPELINE(text)
    ent = next(
        (
            e._.trait
            for e in doc.ents
            if e.label_ == "leaf_size" and e._.trait.part == "leaf"
        ),
        None,
    )
    return ent


def get_size(ent, dim: str = "length") -> Dimension:
    if not ent:
        return Dimension()
    dim_ = next((d for d in ent.dims if d.dim == dim), Dimension())
    return dim_


def vocab_hits(text, vocab, key=None):
    hits = {key: 1} if key and key.lower() in vocab else {}
    hits |= {w: 1 for w in re.split(r"\W+", text) if w.lower() in vocab}
    return " | ".join(hits.keys())


def plants(key, text, rec):
    rec["deciduousness"] = vocab_hits(text, DURATION, key)

    ent = get_ent(text)
    length = get_size(ent, "length")

    rec["plant_height_min_cm"] = length.min
    rec["plant_height_low_cm"] = length.low
    rec["plant_height_high_cm"] = length.high
    rec["plant_height_max_cm"] = length.max


def leaves(_key, text, rec):
    rec["leaf_shape"] = vocab_hits(text, SHAPES)

    ent = get_leaf_size_ent(text)

    length = get_size(ent, "length")
    width = get_size(ent, "width")
    thickness = get_size(ent, "thickness")

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


def seeds(_key, text, rec):
    ent = get_ent(text)

    length = get_size(ent, "length")
    width = get_size(ent, "width")

    rec["seed_length_min_cm"] = length.min
    rec["seed_length_low_cm"] = length.low
    rec["seed_length_high_cm"] = length.high
    rec["seed_length_max_cm"] = length.max

    rec["seed_width_min_cm"] = width.min
    rec["seed_width_low_cm"] = width.low
    rec["seed_width_high_cm"] = width.high
    rec["seed_width_max_cm"] = width.max


def fruits(key, text, rec):
    rec["fruit_type"] = vocab_hits(text, FRUIT_TYPES, key)

    ent = get_ent(text)

    length = get_size(ent, "length")
    width = get_size(ent, "width")

    rec["fruit_length_min_cm"] = length.min
    rec["fruit_length_low_cm"] = length.low
    rec["fruit_length_high_cm"] = length.high
    rec["fruit_length_max_cm"] = length.max

    rec["fruit_width_min_cm"] = width.min
    rec["fruit_width_low_cm"] = width.low
    rec["fruit_width_high_cm"] = width.high
    rec["fruit_width_max_cm"] = width.max


def phenology(info, rec):
    rec["flowering_time"] = info.get("Phenology", "")


def habitat(info, rec):
    rec["habitat"] = info.get("Habitat", "")


def elevation(info, rec):
    text = info.get("Elevation", "")
    ent = get_ent(text)
    elev = get_size(ent, "length")

    rec["elevation_min_m"] = elev.low / 100.0 if elev.low is not None else None
    rec["elevation_max_m"] = elev.high / 100.0 if elev.high is not None else None


def get_terms():
    shape_file = Path(__file__).parent / "terms" / "shapes.csv"
    fruit_file = Path(__file__).parent / "terms" / "fruit_types.csv"
    dur_file = Path(__file__).parent / "terms" / "leaf_duration.csv"

    with shape_file.open() as f:
        shapes = {r["pattern"] for r in csv.DictReader(f)}

    with fruit_file.open() as f:
        fruit_types = {r["pattern"] for r in csv.DictReader(f)}

    with dur_file.open() as f:
        duration = {r["pattern"] for r in csv.DictReader(f)}

    return shapes, fruit_types, duration


PARSE = {
    # Plants
    "Annual": plants,
    "Annual,": plants,
    "Annuals": plants,
    "Annuals,": plants,
    "Biennial": plants,
    "Biennials": plants,
    "Biennials,": plants,
    "Perennial": plants,
    "Perennials": plants,
    "Perennials,": plants,
    "Perennials.": plants,
    "Plants": plants,
    "Shrubs": plants,
    "Shrubs,": plants,
    "Subshrubs": plants,
    "Subshrubs,": plants,
    # Leaves
    "Leaf": leaves,
    "Leaves": leaves,
    "Leaves:": leaves,
    "Cauline": leaves,
    # Fruits
    "Fruits": fruits,
    "Cypselae": fruits,
    # Seeds
    "Seeds": seeds,
    # Unused
    "2n": None,
    "Aerial": None,
    "Arrays": None,
    "Basal": None,
    "Bisexual": None,
    "Bracts": None,
    "Burs": None,
    "Calyculi": None,
    "Corms": None,
    "Corollas": None,
    "Dioecious.": None,
    "Disc": None,
    "Discs": None,
    "Florets": None,
    "Functionally": None,
    "Heads": None,
    "Herbage": None,
    "Inner": None,
    "Innermost": None,
    "Internodes": None,
    "Involucres": None,
    "Outer": None,
    "Ovaries": None,
    "Paleae": None,
    "Pappi": None,
    "Peduncle": None,
    "Peduncles": None,
    "Petioles": None,
    "Phyllaries": None,
    "Phyllary": None,
    "Pistillate": None,
    "Principal": None,
    "Ray": None,
    "Rays": None,
    "Receptacles": None,
    "Receptacular": None,
    "Staminate": None,
    "Stem": None,
    "Stems": None,
    "Stolons": None,
    "Style": None,
    "Taproots": None,
    "Weak": None,
    "Winter": None,
}


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
        metavar="PATH",
        help="""Output the results to this CSV file.""",
    )

    arg_parser.add_argument(
        "--print-keys",
        action="store_true",
        help="""Print a list of treatment keys and exit.""",
    )

    args = arg_parser.parse_args()

    return args


if __name__ == "__main__":
    ARGS = parse_args()
    main(ARGS)
