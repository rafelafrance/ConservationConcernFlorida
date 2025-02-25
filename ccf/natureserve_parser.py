#!/usr/bin/env python3

import argparse
import csv
import textwrap
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from pylib import log
from tqdm import tqdm


def main(args):
    log.started()

    pages = sorted(args.html_dir.glob("*.html"))
    # pages = [p for p in pages if p.stem.startswith("Zizia_aptera")]

    records = []

    for page in tqdm(pages):
        rec = {}

        with page.open() as f:
            page = f.read()

        soup = BeautifulSoup(page, features="lxml")

        for section in soup.find_all("div", attrs={"class": "data-section"}):
            heading = section.find("h2", attrs={"class": "label-div"})

            if not heading:
                continue

            value = section.find("div", attrs={"class": "value-div"})

            parse_sections(heading, rec, value)

        records.append(rec)

    df = pd.DataFrame(records)
    df = sort_columns(df)

    df.to_csv(args.out_csv, index=False)

    log.finished()


def sort_columns(df):
    states = get_states()

    others, canada, usa = [], [], []

    for col in df.columns:
        if col in states and states[col][0] == "Canada":
            state = states[col]
            canada.append((state[1], col))
        elif col in states and states[col][0] == "USA":
            state = states[col]
            usa.append((state[1], col))
        else:
            others.append(col)

    usa = [c[1] for c in sorted(usa)]
    canada = [c[1] for c in sorted(canada)]
    columns = others + usa + canada

    return df[columns]


def get_states():
    canada_file = Path(__file__).parent / "pylib" / "terms" / "canada.csv"
    usa_file = Path(__file__).parent / "pylib" / "terms" / "usa.csv"

    with canada_file.open() as f:
        reader = csv.DictReader(f)
        states = {r["label"]: ("Canada", r["type"]) for r in reader}

    with usa_file.open() as f:
        reader = csv.DictReader(f)
        states |= {r["label"]: ("USA", r["type"]) for r in reader}

    return states


def parse_sections(heading, rec, value):
    match heading.text:
        case "Classification":
            classification_section(rec, value)

        case "Conservation Status":
            conservation_section(rec, value)

        case "Distribution":
            distribution_section(rec, value)

        case "Ecology and Life History":
            ecology_section(rec, value)

    return rec


def ecology_section(rec, value):
    rec |= find_pairs(value)


def distribution_section(rec, value):
    pairs = find_pairs(value)
    rec["Endemism"] = pairs.get("Endemism", "")

    for nation in value.find_all("div", attrs={"class": "nation-list"}):
        if ":" not in nation.text:
            continue
        key, sub_nations = nation.text.split(":")
        sub_nations = sub_nations.strip()
        key = f"Distribution {key}"
        rec[key] = sub_nations


def conservation_section(rec, value):
    for sub_sect in value.find_all("div", attrs={"class": "sub-section-1"}):
        heading = sub_sect.find("h3", attrs={"class": "label-div"})

        pairs = find_pairs(sub_sect)

        match heading.text:
            case "NatureServe Status":
                rec |= {
                    "Global Status": pairs.get("Global Status", ""),
                    "Global Status (Rounded)": pairs.get("Global Status (Rounded)", ""),
                    "Global Status Last Reviewed": pairs.get(
                        "Global Status Last Reviewed", ""
                    ),
                    "Rank Method Used": pairs.get("Rank Method Used", ""),
                    "Reasons": pairs.get("Reasons", ""),
                }

            case "National & State/Provincial Statuses":
                for nation in value.find_all("div", attrs={"class": "nation-data"}):
                    rec |= find_pairs(nation)

            case "Other Statuses":
                rec |= pairs

            case "NatureServe Global Conservation Status Factors":
                rec |= {
                    "Range Extent": pairs.get("Range Extent", ""),
                    "Area of Occupancy": pairs.get("Area of Occupancy", ""),
                    "Area of Occupancy Comments": pairs.get(
                        "Area of Occupancy Comments", ""
                    ),
                    "Degree of Threat": pairs.get("Degree of Threat", ""),
                    "Threat Comments": pairs.get("Threat Comments", ""),
                    "Long-term Trend": pairs.get("Long-term Trend", ""),
                    "Long-term Trend Comments": pairs.get(
                        "Long-term Trend Comments", ""
                    ),
                    "Short-term Trend": pairs.get("Short-term Trend", ""),
                    "Short-term Trend Comments": pairs.get(
                        "Short-term Trend Comments", ""
                    ),
                }

    for nation in value.find_all("div", attrs={"class": "nation-data"}):
        rec |= find_pairs(nation)


def classification_section(rec, value):
    pairs = find_pairs(value)
    rec |= {
        "Scientific Name": pairs["Scientific Name"],
        "Order": pairs["Order"],
        "Family": pairs["Family"],
        "Genus": pairs["Genus"],
        "NatureServe Unique Identifier": pairs.get("NatureServe Unique Identifier"),
    }


def find_pairs(soup):
    pairs = {}
    for pair in soup.find_all("div", attrs={"class": "data-pair"}):
        label = pair.find("div", attrs={"class": "label-div"}).text
        label = label.replace(":", "").strip()

        value = pair.find("div", attrs={"class": "value-div"}).text
        value = value.strip()
        value = "" if value == "None" else value

        pairs[label] = value

    return pairs


def parse_args():
    arg_parser = argparse.ArgumentParser(
        allow_abbrev=True,
        description=textwrap.dedent("Parse data from downloaded HTML files."),
    )

    arg_parser.add_argument(
        "--nature-serve-json",
        type=Path,
        required=True,
        metavar="PATH",
        help="""Parse the data in this downloaded NatureServe JSON list page.""",
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
