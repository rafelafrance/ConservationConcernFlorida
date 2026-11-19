#!/bin/bash

stamp=$(date +%y%m%d)

uv run ccf/natureserve_threats_2_revise.py \
    --in-csv data/threats/nature_serve_26q3a.csv \
    --threat-csv data/threats/threats_nature_serve_1a_261117_gemma.csv \
    --out-csv data/threats/threats_nature_serve_2_"$stamp"_gemma.csv \
    --prompt prompts/iucn_threats_revised.md \
    --threads 4 \
    --log-file data/threats/nature_serve_threats.log

    # --out-csv data/threats/threats_nature_serve_"$stamp".csv \
    # --out-csv data/threats/threats_nature_serve_261012.csv \
