#!/bin/bash

stamp=$(date +%y%m%d)

uv run ccf/natureserve_threats.py \
    --in-csv data/threats/nature_serve_26q3a.csv \
    --out-csv data/threats/threats_nature_serve_261012.csv \
    --prompt-dir prompts/iucn_threats \
    --threads 4 \
    --limit 2000 \
    --log-file data/threats/nature_serve_threats.log

    # --out-csv data/threats/threats_nature_serve_"$stamp".csv \
