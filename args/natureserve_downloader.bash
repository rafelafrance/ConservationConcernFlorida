#!/bin/bash

uv run ccf/natureserve_downloader.py \
    --target-taxa-csv data/natureserve/export_260722_rand.csv \
    --nature-serve-json data/natureserve/nsExplorer-Export-2026-07-22-04-26_AllNorthA_angio_gymno.json \
    --html-dir data/natureserve/pages_26q3
