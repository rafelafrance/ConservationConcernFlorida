#!/bin/bash

uv run ccf/natureserve_downloader.py \
    --target-taxa-csv data/natureserve/random100.csv \
    --nature-serve-json data/natureserve/nsExplorer-Export-2026-07-22-04-26_AllNorthA_angio_gymno.json \
    --html-dir data/natureserve/pages_260723
