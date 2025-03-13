#!/usr/bin/env python3

import argparse
import json
import re
import textwrap
from dataclasses import asdict
from pathlib import Path

import ftfy
from bs4 import BeautifulSoup
from pylib import log, pipeline
from pylib.lm_data import Example
from rules.size import Size
from tqdm import tqdm

PIPELINE = pipeline.build()


def main(args):
    log.started()

    pages = sorted(args.html_dir.glob("*.html"))

    records = []

    for page in tqdm(pages):
        with page.open() as f:
            text = f.read()

        soup = BeautifulSoup(text, features="lxml")

        treatment, treatment_text = get_treatment(soup)
        info = get_info(soup)

        taxon = page.stem.replace("_", " ")
        taxon = taxon[0].upper() + taxon[1:]

        rec = Example(
            taxon=clean(taxon).replace("×", "x "),
            text=treatment_text + info_text(info),
        )

        used = set()

        for key, value in treatment.items():
            if (func := PARSE.get(key)) and func not in used:
                used.add(func)  # Only use a parse function once
                func(key, value, rec)

        phenology(info, rec)
        habitat(info, rec)
        elevation(info, rec)

        records.append(asdict(rec))

    with args.out_json.open("w") as f:
        json.dump(records, f, indent=4)

    log.finished()


def get_treatment(soup) -> tuple[dict[str, str], str]:
    treatment = soup.find("span", class_="statement")
    if not treatment:
        return {}, ""

    treatment = [str(c) for c in treatment.contents]

    text = "".join(treatment)
    text = clean(text).replace("<i>", "").replace("</i>", "")

    soup2 = BeautifulSoup(text, features="lxml")
    parts = [p.text.strip() for p in soup2.find_all(string=True)]
    parts = dict(zip(parts[0::2], parts[1::2], strict=True))

    return parts, text


def get_info(soup):
    info = soup.find("div", class_="treatment-info").find_all(string=True)
    info = [clean(x) for i in info if (x := i.strip()) and i.find(":") > -1]
    info = {i.split(":")[0].strip(): i.split(":")[1].strip() for i in info}
    return info


def info_text(info) -> str:
    text = ""
    for key in ("Phenology", "Habitat", "Elevation"):
        if info.get(key, ""):
            text += "\n" + key + ": " + info[key]
    return text


def clean(text):
    text = ftfy.fix_text(text)  # Handle common mojibake
    # text = re.sub(r"[–—\-]+", "-", text)
    # text = text.replace("±", "+/-")
    # text = text.replace("×", "x")
    return text


def get_size_trait(doc, label: str, part: str) -> Size:
    ent = next(
        (e._.trait for e in doc.ents if e.label_ == label and e._.trait.part == part),
        None,
    )
    if not ent:
        ent = next((e._.trait for e in doc.ents if e.label_ == "size"), Size())
    return ent


def get_size_dim(size, text, dim: str) -> str:
    dim_ = next((d for d in size.dims if d.dim == dim), None)
    value = ""
    if dim_:
        value = text[dim_.start : dim_.end]
        value = re.sub(r"[.]$", "", value)
        value += "" if value.endswith(dim_.units) else f" {dim_.units}"
    return value


def vocab_hits(doc, trait: str) -> str:
    start, end = -1, -1

    for ent in doc.ents:
        if ent.label_ == trait:
            start = doc[ent.start].idx if start == -1 else start
            end = doc[ent.end - 1].idx + len(doc[ent.end - 1])

        # Don't cross another entity
        elif ent.label_ != trait and start != -1:
            break

    value = doc.text[start:end] if start != -1 else ""
    return value


def plants(_key, text, rec: Example):
    doc = PIPELINE(text)
    rec.deciduousness = vocab_hits(doc, "leaf_duration")

    size = get_size_trait(doc, "", "")
    rec.plant_height = get_size_dim(size, text, "length")


def leaves(_key, text, rec: Example):
    doc = PIPELINE(text)

    rec.leaf_shape = vocab_hits(doc, "shape")

    size = get_size_trait(doc, "leaf_size", "leaf")

    rec.leaf_length = get_size_dim(size, text, "length")
    rec.leaf_width = get_size_dim(size, text, "width")
    rec.leaf_thickness = get_size_dim(size, text, "thickness")


def seeds(_key, text, rec: Example):
    doc = PIPELINE(text)
    size = get_size_trait(doc, "seed_size", "seed")

    rec.seed_length = get_size_dim(size, text, "length")
    rec.seed_width = get_size_dim(size, text, "width")


def fruits(key, text, rec: Example):
    doc = PIPELINE(f"{key} {text}")
    rec.fruit_type = vocab_hits(doc, "fruit_type")

    size = get_size_trait(doc, "fruit_size", "fruit")

    rec.fruit_length = get_size_dim(size, text, "length")
    rec.fruit_width = get_size_dim(size, text, "width")


def phenology(info, rec: Example):
    value = info.get("Phenology", "")
    value = re.sub(r"[.]$", "", value)
    rec.phenology = value


def habitat(info, rec: Example):
    rec.habitat = info.get("Habitat", "")


def elevation(info, rec: Example):
    text = info.get("Elevation", "")
    doc = PIPELINE(text)
    size = get_size_trait(doc, "", "")
    rec.elevation = get_size_dim(size, text, "length")


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
        description=textwrap.dedent(
            "Make LM training data from downloaded HTML files."
        ),
    )

    arg_parser.add_argument(
        "--html-dir",
        type=Path,
        required=True,
        metavar="PATH",
        help="""Parse HTML files in this directory.""",
    )

    arg_parser.add_argument(
        "--out-json",
        type=Path,
        metavar="PATH",
        help="""Output the results to this JSON file.""",
    )

    args = arg_parser.parse_args()

    return args


if __name__ == "__main__":
    ARGS = parse_args()
    main(ARGS)
