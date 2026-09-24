#!/bin/bash

stamp=$(date +%y%m%d)

uv run ccf/natureserve_threats.py \
    --in-csv data/threats/nature_serve_26q3a.csv \
    --out-csv data/threats/threats_nature_serve_"$stamp".csv \
    --reasoning-effort none \
    --threads 4 \
    --limit 1000 \
    --log-file data/threats/nature_serve_threats.log
