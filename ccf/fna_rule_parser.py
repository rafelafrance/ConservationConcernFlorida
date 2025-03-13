#!/usr/bin/env python3

import argparse
import csv
import re
import textwrap
from pathlib import Path

import ftfy
import pandas as pd
from bs4 import BeautifulSoup
from pylib import log, pipeline
from rules.size import Dimension, Size
from tqdm import tqdm

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

    for page in tqdm(pages):
        with page.open() as f:
            text = f.read()

        soup = BeautifulSoup(text, features="lxml")

        treat = get_treatment(soup)

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
    text = re.sub(r"[–—\-]+", "-", text)
    text = text.replace("±", "+/-")
    text = text.replace("×", "x")
    return text


def get_size_trait(text: str, label: str, part: str) -> Size:
    doc = PIPELINE(text)
    ent = next(
        (e._.trait for e in doc.ents if e.label_ == label and e._.trait.part == part),
        None,
    )
    if not ent:
        ent = next((e._.trait for e in doc.ents if e.label_ == "size"), Size())
    return ent


def get_size_dim(size, dim: str = "length") -> Dimension:
    if not size:
        return Dimension()
    dim_ = next((d for d in size.dims if d.dim == dim), Dimension())
    return dim_


def vocab_hits(text, vocab, key=None):
    hits = {key: 1} if key and key.lower() in vocab else {}
    hits |= {w: 1 for w in re.split(r"\W+", text) if w.lower() in vocab}
    return " | ".join(hits.keys())


def plants(key, text, rec):
    rec["deciduousness"] = vocab_hits(text, DURATION, key)

    size = get_size_trait(text, "", "")
    size = Size.convert_units_to_cm(size)

    length = get_size_dim(size, "length")

    rec["plant_height_min_cm"] = length.min
    rec["plant_height_low_cm"] = length.low
    rec["plant_height_high_cm"] = length.high
    rec["plant_height_max_cm"] = length.max


def leaves(_key, text, rec):
    rec["leaf_shape"] = vocab_hits(text.lower(), SHAPES)

    size = get_size_trait(text, "leaf_size", "leaf")
    size = Size.convert_units_to_cm(size)

    length = get_size_dim(size, "length")
    width = get_size_dim(size, "width")
    thickness = get_size_dim(size, "thickness")

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
    size = get_size_trait(text, "seed_size", "seed")
    size = Size.convert_units_to_cm(size)

    length = get_size_dim(size, "length")
    width = get_size_dim(size, "width")

    rec["seed_length_min_cm"] = length.min
    rec["seed_length_low_cm"] = length.low
    rec["seed_length_high_cm"] = length.high
    rec["seed_length_max_cm"] = length.max

    rec["seed_width_min_cm"] = width.min
    rec["seed_width_low_cm"] = width.low
    rec["seed_width_high_cm"] = width.high
    rec["seed_width_max_cm"] = width.max


def fruits(key, text, rec):
    rec["fruit_type"] = vocab_hits(text.lower(), FRUIT_TYPES, key.lower())

    size = get_size_trait(text, "fruit_size", "fruit")
    size = Size.convert_units_to_cm(size)

    length = get_size_dim(size, "length")
    width = get_size_dim(size, "width")

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
    size = get_size_trait(text, "", "")
    elev = get_size_dim(size, "length")

    rec["elevation_min_m"] = elev.low
    rec["elevation_max_m"] = elev.high


def get_terms():
    shape_file = Path(__file__).parent / "rules" / "terms" / "shape_terms.csv"
    fruit_file = Path(__file__).parent / "rules" / "terms" / "fruit_terms.csv"
    dur_file = Path(__file__).parent / "rules" / "terms" / "leaf_terms.csv"

    with shape_file.open() as f:
        shapes = {r["pattern"] for r in csv.DictReader(f)}

    with fruit_file.open() as f:
        fruit_types = {
            r["pattern"] for r in csv.DictReader(f) if r["label"] == "fruit_type"
        }
    fruit_types -= {"fruit", "fruits"}

    with dur_file.open() as f:
        duration = {
            r["pattern"] for r in csv.DictReader(f) if r["label"] == "leaf_duration"
        }

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

    args = arg_parser.parse_args()

    return args


if __name__ == "__main__":
    ARGS = parse_args()
    main(ARGS)
