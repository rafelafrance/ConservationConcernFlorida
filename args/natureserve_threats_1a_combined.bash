#!/bin/bash

stamp=$(date +%y%m%d)

uv run ccf/natureserve_threats_1a_combined.py \
    --in-csv data/threats/nature_serve_26q3a.csv \
    --out-csv data/threats/threats_nature_serve_"$stamp".csv \
    --prompt prompts/iucn_threats.md \
    --threads 4 \
    --max-tokens 32768 \
    --limit 2000 \
    --log-file data/threats/nature_serve_threats.log

    # --out-csv data/threats/threats_nature_serve_"$stamp".csv \
    # --out-csv data/threats/threats_nature_serve_261012.csv \
