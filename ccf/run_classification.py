#!/usr/bin/env python3
"""
Batch-process nature_serve_26q3a.csv: classify the four threat-text columns.

(Reasons, Threat Comments, Long-term Trend Comments, Short-term Trend Comments)
with the IUCN classifier and emit:

  1. nature_serve_26q3a_threats.json  — for programmers.
       { "<Scientific Name>": { "<SourceCol>": [entries...], ... }, ... }
       (also keeps "_meta" key with column order etc.)

  2. nature_serve_26q3a_threats.csv   — for researchers.
       All 110 original columns, then for each of the four source columns,
       two derived columns immediately after it:
         <Source>_category_names  — semicolon-joined set of category names
         <Source>_category_ids    — semicolon-joined set of category ids
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from classify_threats import classify

SRC = Path("data/threats/nature_serve_26q3a.csv")
OUT_JSON = Path("data/threats/nature_serve_26q3a_threats.json")
OUT_CSV = Path("data/threats/nature_serve_26q3a_threats.csv")

# The four text columns to classify, in output order.
SOURCE_COLS = [
    "Reasons",
    "Threat Comments",
    "Long-term Trend Comments",
    "Short-term Trend Comments",
]


def derived_names(col: str) -> tuple[str, str]:
    return f"{col}_category_names", f"{col}_category_ids"


def sets_from_entries(entries: list[dict]) -> tuple[str, str]:
    """Return (names_joined, ids_joined) as semicolon-joined, deduped, sorted."""
    ids = sorted({e["category_id"] for e in entries})
    names = sorted({e["category_name"] for e in entries})
    return ";".join(names), ";".join(str(i) for i in ids)


def main() -> None:
    with SRC.open(newline="") as f:
        reader = csv.DictReader(f)
        original_fields = list(reader.fieldnames)
        rows = list(reader)

    # Build the new field order: original fields, with derived columns inserted
    # immediately after each source column.
    new_fields = list(original_fields)
    for col in SOURCE_COLS:
        idx = new_fields.index(col)
        n, i = derived_names(col)
        new_fields.insert(idx + 1, i)
        new_fields.insert(idx + 1, n)
    # Reorder so names comes before ids (we inserted ids first then names at same pos)
    # Actually we inserted ids at idx+1, then names at idx+1 which pushes ids to idx+2.
    # So order is: col, names, ids. Good.

    json_out = {}
    with OUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=new_fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            sp = row.get("Scientific Name", "")
            json_row = {}
            csv_row = dict(row)
            for col in SOURCE_COLS:
                text = row.get(col) or ""
                entries = classify(text)
                json_row[col] = entries
                names, ids = sets_from_entries(entries)
                n_col, i_col = derived_names(col)
                csv_row[n_col] = names
                csv_row[i_col] = ids
            json_out[sp] = json_row
            writer.writerow(csv_row)

    # Write JSON with a small meta block
    payload = {
        "_meta": {
            "source_file": str(SRC),
            "source_columns": SOURCE_COLS,
            "classifier": "IUCN v3.2 (12 major categories) — data/threats/classify_threats.py",
            "n_species": len(json_out),
        },
        **json_out,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    print(f"Wrote {OUT_JSON}  ({len(json_out)} species)")
    print(f"Wrote {OUT_CSV}   ({len(new_fields)} columns)")


if __name__ == "__main__":
    main()
