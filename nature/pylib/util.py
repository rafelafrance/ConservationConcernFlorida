import csv
import json
from pathlib import Path
from pprint import pp

BASE_URL = "https://explorer.natureserve.org"


def get_target_taxa(target_taxa_csv: Path) -> list[str]:
    with target_taxa_csv.open() as f:
        reader = csv.DictReader(f)
        targets = {r["parentTaxon"] for r in reader}
    return sorted(targets)


def get_nature_serve_taxa(nature_serve_json: Path) -> dict[str, dict]:
    """Get a dict of nature serve taxa/synonyms and nature_serve records."""
    with nature_serve_json.open() as f:
        data = json.load(f)

    nature_serve = {}
    for item in data:
        nature_serve[item["scientificName"]] = item
        species_global = item.get("speciesGlobal", {})
        synomnyms = species_global.get("synonyms", [])
        for syn in synomnyms:
            syn = " ".join(syn.split()[:2])
            nature_serve[syn] = item

    return nature_serve


def get_download_file_name(nature_serve_rec: dict, parent: Path) -> Path:
    id_ = nature_serve_rec["elementGlobalId"]
    taxon = nature_serve_rec["scientificName"]
    taxon = taxon.replace(" ", "_")
    return parent / f"{taxon}_{id_}.html"


def get_download_url(nature_serve_rec: dict) -> str:
    return f"{BASE_URL}{nature_serve_rec['nsxUrl']}"


def compare_targets_and_nature_serve(
    targets: list[str], nature_serve: dict[str, dict]
) -> None:
    hits = 0
    misses = []
    for target in targets:
        hits += 1 if target in nature_serve else 0
        if target not in nature_serve:
            misses.append(target)

    print(f"Nature  {len(nature_serve)}")
    print(f"targets {len(targets)}")
    print(f"hits    {hits}")

    pp(sorted(misses))
