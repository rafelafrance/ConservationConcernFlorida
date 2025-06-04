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
        # print(page.stem)
        with page.open() as f:
            text = f.read()

        soup = BeautifulSoup(text, features="lxml")

        treatment = get_treatment(soup)

        taxon = page.stem.replace("_", " ")
        taxon = taxon[0].upper() + taxon[1:]
        rec = {"taxon": clean(taxon).replace("×", "x ")}

        used = set()

        for key, text in treatment.items():
            if funcs := PARSE.get(key):
                for func in funcs:
                    if func not in used and func(key, text, rec):
                        used.add(func)  # Only parse a function once

        info = get_info(soup)
        if info:
            phenology(info, rec)
            habitat(info, rec)
            elevation(info, rec)

        records.append(rec)

    pd.DataFrame(records).to_csv(args.out_csv, index=False)

    log.finished()


def parse_treatment(rec, treatment):
    used = set()

    for key, text in treatment.items():
        if funcs := PARSE.get(key):
            for func in funcs:
                if func not in used and func(key, text, rec):
                    used.add(func)  # Only parse a function once


def has_value(dim):
    return any(getattr(dim, k) is not None for k in ("min", "low", "high", "max"))


def plant_height(_key, text, rec):
    size = get_size_trait(text, "", "")
    size = Size.convert_units_to_cm(size)

    length = get_size_dim(size, "length")

    rec["plant_height_min_cm"] = length.min
    rec["plant_height_low_cm"] = length.low
    rec["plant_height_high_cm"] = length.high
    rec["plant_height_max_cm"] = length.max

    return has_value(length)


def plant_deciduousness(key, text, rec):
    rec["deciduousness"] = vocab_hits(text, DURATION, key)
    return bool(rec["deciduousness"])


def leaf_size(_key, text, rec):
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

    return has_value(length) or has_value(width) or has_value(thickness)


def leaf_shape(_key, text, rec):
    rec["leaf_shape"] = vocab_hits(text.lower(), SHAPES)
    return bool(rec["leaf_shape"])


def seed_size(_key, text, rec):
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

    return has_value(length) or has_value(width)


def fruit_type(key, text, rec):
    rec["fruit_type"] = vocab_hits(text.lower(), FRUIT_TYPES, key.lower())
    return bool(rec["fruit_type"])


def fruit_size(_key, text, rec):
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

    return has_value(length) or has_value(width)


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


def get_treatment(soup):
    treatment = soup.find("span", class_="statement")
    if not treatment:
        return {}

    text = str(treatment).replace("<i>", "").replace("</i>", "")
    text = re.sub(r"(Perennials|Annuals|Biennials);", r"<b>\1</b>", text)
    text = clean(text)

    soup2 = BeautifulSoup(text, features="lxml")
    parts = [p.text.strip() for p in soup2.find_all(string=True)]
    treatment = dict(zip(parts[0::2], parts[1::2], strict=True))
    return treatment


def get_info(soup):
    info = soup.find("div", class_="treatment-info")
    if not info:
        return None
    info = info.find_all(string=True)
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
    "Culm": (plant_height, plant_deciduousness),
    "Culms": (plant_height, plant_deciduousness),
    "Annual": (plant_height, plant_deciduousness),
    "Annual,": (plant_height, plant_deciduousness),
    "Annuals": (plant_height, plant_deciduousness),
    "Annuals,": (plant_height, plant_deciduousness),
    "Annuals.": (plant_height, plant_deciduousness),
    "Biennial": (plant_height, plant_deciduousness),
    "Biennials": (plant_height, plant_deciduousness),
    "Biennials,": (plant_height, plant_deciduousness),
    "Herb": (plant_height, plant_deciduousness),
    "Herb,": (plant_height, plant_deciduousness),
    "Herbage": (plant_height, plant_deciduousness),
    "Herbs": (plant_height, plant_deciduousness),
    "Herbs,": (plant_height, plant_deciduousness),
    "Herbs.": (plant_height, plant_deciduousness),
    "Herbs:": (plant_height, plant_deciduousness),
    "Perennial": (plant_height, plant_deciduousness),
    "Perennials": (plant_height, plant_deciduousness),
    "Perennials,": (plant_height, plant_deciduousness),
    "Perennials.": (plant_height, plant_deciduousness),
    "Plant": (plant_height, plant_deciduousness),
    "Plants": (plant_height, plant_deciduousness),
    "Shrubs": (plant_height, plant_deciduousness),
    "Shrubs,": (plant_height, plant_deciduousness),
    "Subshrubs": (plant_height, plant_deciduousness),
    "Subshrubs,": (plant_height, plant_deciduousness),
    "Subshrubs.": (plant_height, plant_deciduousness),
    "Trees": (plant_height, plant_deciduousness),
    "Trees,": (plant_height, plant_deciduousness),
    "Vines": (plant_height, plant_deciduousness),
    "Vines,": (plant_height, plant_deciduousness),
    "Winter": (plant_height, plant_deciduousness),
    # Leaves
    "Blades": (leaf_size, leaf_shape),
    "Sheaths": (leaf_size, leaf_shape),
    "Leaf": (leaf_size, leaf_shape),
    "Leaves": (leaf_size, leaf_shape),
    "Leaves:": (leaf_size, leaf_shape),
    "Foliage": (leaf_size, leaf_shape),
    "Cauline": (leaf_size, leaf_shape),
    "Fronds": (leaf_size, leaf_shape),
    "Topknots": (leaf_size, leaf_shape),
    # Fruits
    "Fruits": (fruit_size, fruit_type),
    "Fruiting": (fruit_size, fruit_type),
    "Acorns": (fruit_size, fruit_type),
    "Achene": (fruit_size, fruit_type),
    "Achenes": (fruit_size, fruit_type),
    "Berries": (fruit_size, fruit_type),
    "Capsules": (fruit_size, fruit_type),
    "Capules": (fruit_size, fruit_type),
    "Caryopses": (fruit_size, fruit_type),
    "Cypselae": (fruit_size, fruit_type),
    "Drupes": (fruit_size, fruit_type),
    "Loments": (fruit_size, fruit_type),
    "Legumes": (fruit_size, fruit_type),
    "Mericarps": (fruit_size, fruit_type),
    "Pappi": (fruit_size, fruit_type),
    "Pomes": (fruit_size, fruit_type),
    "Schizocarps": (fruit_size, fruit_type),
    "Utricles": (fruit_size, fruit_type),
    # Seeds
    "Seed": (seed_size,),
    "Seeds": (seed_size,),
    # Unused
    "2n": None,
    "Aerial": None,
    "Anthers": None,
    "Anthesis": None,
    "Arrays": None,
    "Bark": None,
    "Barneby": None,
    "Basal": None,
    "Bisexual": None,
    "Both": None,
    "Bracteoles": None,
    "Bracts": None,
    "Buds": None,
    "Bulb": None,
    "Bulbs": None,
    "Burs": None,
    "Callus": None,
    "Calluses": None,
    "Calyces": None,
    "Calyculi": None,
    "Cataphylls": None,
    "Central": None,
    "Chasmogamous": None,
    "Chromosome": None,
    "Cialdella": None,
    "Cleistogamous": None,
    "Corms": None,
    "Corollas": None,
    "Coty": None,
    "Cotyledons": None,
    "Cyathia": None,
    "Cyathial": None,
    "Dietrich": None,
    "Dioecious.": None,
    "Disc": None,
    "Discs": None,
    "Duffield": None,
    "Fertile": None,
    "Fla": None,
    "Floral": None,
    "Florets": None,
    "Flow": None,
    "Flowers": None,
    "Fol": None,
    "Follicles": None,
    "Friesner": None,
    "Functionally": None,
    "Glomes": None,
    "Glumes": None,
    "Green": None,
    "Heads": None,
    "Hips": None,
    "In": None,
    "Inflo": None,
    "Inflores": None,
    "Inflorescence": None,
    "Inflorescences": None,
    "Inflorescnecs": None,
    "Infructescences": None,
    "Inner": None,
    "Innermost": None,
    "Internodes": None,
    "Involucellar": None,
    "Involucre": None,
    "Involucres": None,
    "Irwin": None,
    "Lateral": None,
    "Latex": None,
    "Leaflets": None,
    "Lemmas": None,
    "Lianas": None,
    "Ligules": None,
    "Lower": None,
    "Marazzi": None,
    "Mature": None,
    "Oenothera": None,
    "Outer": None,
    "Ovaries": None,
    "Paleae": None,
    "Panicles": None,
    "Pedi": None,
    "Pedicellate": None,
    "Pedicels": None,
    "Peduncle": None,
    "Peduncles": None,
    "Perigynia": None,
    "Petioles": None,
    "Phyllaries": None,
    "Phyllary": None,
    "Pistillate": None,
    "Primary": None,
    "Principal": None,
    "Proximal": None,
    "Pseudobulbs": None,
    "Racemes": None,
    "Rames": None,
    "Ray": None,
    "Rays": None,
    "Receptacles": None,
    "Receptacular": None,
    "Rhizomal": None,
    "Rhizome": None,
    "Rhizomes": None,
    "Roots": None,
    "Scales": None,
    "Scape": None,
    "Scapes": None,
    "Senna": None,
    "Sessile": None,
    "Spathe": None,
    "Spike": None,
    "Spikelets": None,
    "Spikes": None,
    "Stamens": None,
    "Stamimate": None,
    "Staminate": None,
    "Stem": None,
    "Stems": None,
    "Stigmas": None,
    "Stipes": None,
    "Stolons": None,
    "Style": None,
    "Subspecies": None,
    "Subterranean": None,
    "Taproots": None,
    "Terminal": None,
    "The": None,
    "Three": None,
    "Thyrses": None,
    "Tubercles": None,
    "Tubers": None,
    "Twigs": None,
    "Umbel": None,
    "Umbels": None,
    "Upper": None,
    "Variety": None,
    "Wagner": None,
    "Weak": None,
    "Wipff": None,
    "Woody": None,
    "Xylopodium:": None,
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
