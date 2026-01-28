#!/usr/bin/env python3

import argparse
import json
import re
import textwrap
from pathlib import Path

import ftfy
from bs4 import BeautifulSoup
from pylib import fna_parse_treatment as parser
from pylib import log, pipeline
from pylib.trait_extractor import TraitExtractor
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

        rec = TraitExtractor(
            family=args.family.title(),
            taxon=clean(taxon).replace("×", "x "),
            text=treatment_text + info_text(info),
        )

        used = set()

        for key, value in treatment.items():
            if (func := parser.PARSE.get(key)) and func not in used:
                used.add(func)  # Only use a parse function once
                func(key, value, rec)

        phenology(info, rec)
        habitat(info, rec)
        elevation(info, rec)

        record = {k: v for k, v in rec.model_dump().items() if k != "prompt"}

        records.append(record)

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


def plants(_key, text, rec: TraitExtractor):
    doc = PIPELINE(text)
    rec.deciduousness = vocab_hits(doc, "leaf_duration")

    size = get_size_trait(doc, "", "")
    rec.plant_height = get_size_dim(size, text, "length")


def leaves(_key, text, rec: TraitExtractor):
    doc = PIPELINE(text)

    rec.leaf_shape = vocab_hits(doc, "shape")

    size = get_size_trait(doc, "leaf_size", "leaf")

    rec.leaf_length = get_size_dim(size, text, "length")
    rec.leaf_width = get_size_dim(size, text, "width")
    rec.leaf_thickness = get_size_dim(size, text, "thickness")


def seeds(_key, text, rec: TraitExtractor):
    doc = PIPELINE(text)
    size = get_size_trait(doc, "seed_size", "seed")

    rec.seed_length = get_size_dim(size, text, "length")
    rec.seed_width = get_size_dim(size, text, "width")


def fruits(key, text, rec: TraitExtractor):
    key_doc = PIPELINE(key)
    doc = PIPELINE(text)
    key_type = vocab_hits(key_doc, "fruit_type")
    fruit_type = vocab_hits(doc, "fruit_type")

    rec.fruit_type = key_type
    rec.fruit_type += " " if key_type and fruit_type else ""
    rec.fruit_type += fruit_type

    size = get_size_trait(doc, "fruit_size", "fruit")

    rec.fruit_length = get_size_dim(size, text, "length")
    rec.fruit_width = get_size_dim(size, text, "width")


def phenology(info, rec: TraitExtractor):
    value = info.get("Phenology", "")
    value = re.sub(r"[.]$", "", value)
    rec.phenology = value


def habitat(info, rec: TraitExtractor):
    rec.habitat = info.get("Habitat", "")


def elevation(info, rec: TraitExtractor):
    text = info.get("Elevation", "")
    doc = PIPELINE(text)
    size = get_size_trait(doc, "", "")
    rec.elevation = get_size_dim(size, text, "length")


def parse_args():
    arg_parser = argparse.ArgumentParser(
        allow_abbrev=True,
        description=textwrap.dedent(
            """
            Create DSPy training data from rule parses.

            Given the output from fna_rule_parser.py convert it into a format that
            DSPy can use for "training" models.
            """
        ),
    )

    arg_parser.add_argument(
        "--family",
        type=Path,
        required=True,
        metavar="PATH",
        help="""Get fna_rule_parser.py results from this CSV file.""",
    )

    arg_parser.add_argument(
        "--out-json",
        type=Path,
        metavar="PATH",
        help="""Output the training data to this JSON file.""",
    )

    args = arg_parser.parse_args()

    return args


if __name__ == "__main__":
    ARGS = parse_args()
    main(ARGS)
