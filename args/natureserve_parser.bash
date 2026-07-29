#!/bin/bash

uv run ccf/natureserve_parser.py \
    --nature-serve-json data/natureserve/nsExplorer-Export-2026-07-22-04-26_AllNorthA_angio_gymno.json \
    --html-dir data/natureserve/pages_26q3 \
    --out-csv data/natureserve/parsed_test.csv
