#!/usr/bin/env python

import argparse
import csv
import json
import logging
import os
import re
import textwrap
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from json.decoder import JSONDecodeError
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from requests.exceptions import RequestException
from tqdm import tqdm

from ccf.pylib import log

FIELDS = [
    "Reasons",
    "Threat Comments",
    "Long-term Trend Comments",
    "Short-term Trend Comments",
]

# Input columns from args.in_csv
IN_COLUMNS = [
    "Scientific Name",
    "Order",
    "Family",
    "Genus",
    "NatureServe Unique Identifier",
    "Global Status",
    "Global Status (Rounded)",
    *FIELDS,
]

# Output columns to args.out_csv
OUT_COLUMNS = [
    "status",
    "Scientific Name",
    "Order",
    "Family",
    "Genus",
    "NatureServe Unique Identifier",
    "Global Status",
    "Global Status (Rounded)",
    *FIELDS,
    "threat_status",
    "threat_categories",
    "threat_category_count",
    "threat_mentions",
]

BUFFER_COLUMNS = [
    "status",
    "sci_name",
    "category",
    "mentions",
]

CATEGORY_ORDER = [
    "1. Residential & Commercial Development",
    "2. Agriculture & Aquaculture",
    "3. Energy Production & Mining",
    "4. Transportation & Service Corridors",
    "5. Biological Resource Use",
    "6. Human Intrusions & Disturbance",
    "7. Natural System Modifications",
    "8. Invasive & Problematic Species and Diseases",
    "9. Pollution",
    "10. Geological Events",
    "11. Climate Change & Severe Weather",
    "12. Other",
]


@dataclass
class CategoryPrompt:
    name: str
    prompt: str
    json_schema: str


@dataclass
class ModelArgs:
    model_id: str = "unsloth/Qwen3.8-27B-GGUF"
    api_host: str = "http://localhost:9931/v1"
    timeout: int = 300
    threads: int = 1


def load_category_prompts(prompt_dir: Path) -> list[CategoryPrompt]:
    if not prompt_dir.is_dir():
        raise SystemExit(f"Prompt directory not found: {prompt_dir}")
    prompts = []
    for path in sorted(prompt_dir.glob("*.md")):
        text = path.read_text()
        front = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
        if not front:
            raise SystemExit(f"{path}: missing frontmatter")
        cat = re.search(r"^category:\s*(.+?)\s*$", front.group(1), flags=re.MULTILINE)
        if not cat:
            raise SystemExit(f"{path}: missing 'category' frontmatter field")
        name = cat.group(1).strip().strip('"')
        body = re.sub(r"^---$.*^---$", "", text, flags=re.MULTILINE | re.DOTALL).strip()
        schema = re.search(r"```json(.+)```", body, flags=re.DOTALL)
        if not schema:
            raise SystemExit(f"{path}: missing json schema block")
        prompts.append(CategoryPrompt(name, body, schema.group(1).strip()))
    names = [p.name for p in prompts]
    missing = [n for n in CATEGORY_ORDER if n not in names]
    extra = [n for n in names if n not in CATEGORY_ORDER]
    if missing:
        raise SystemExit(f"{prompt_dir}: missing category prompts: {missing}")
    if extra:
        raise SystemExit(f"{prompt_dir}: unexpected category prompts: {extra}")
    return prompts


def classify_threats(args: argparse.Namespace) -> None:
    job_began = log.job_began(args.log_file, args=args)

    in_data = pd.read_csv(args.in_csv, dtype=str, usecols=IN_COLUMNS)
    in_data = in_data.fillna("").to_dict("records")
    in_data = [t for t in in_data if t.get("Scientific Name")]
    in_data = in_data[: args.limit]
    for row in in_data:
        row["target"] = "\n\n".join([t for f in FIELDS if (t := row.get(f))]) or ""
    in_data = {t["Scientific Name"]: t for t in in_data}

    buff_file = args.out_csv.with_stem(args.out_csv.stem + "_buffer")
    already_read = {}
    buff_mode = "w"
    if buff_file.exists():
        buff_mode = "a"
        with buff_file.open() as buff_csv:
            reader = csv.DictReader(buff_csv)
            already_read = {(r["Scientific Name"], r["category"]) for r in reader}

    category_prompts = load_category_prompts(args.prompt_dir)

    statuses = defaultdict(int)

    model_args = ModelArgs(
        model_id=args.model_id,
        api_host=args.api_host,
        timeout=args.timeout,
        threads=args.threads,
    )

    with buff_file.open(buff_mode) as buff_fh:
        writer = csv.DictWriter(buff_fh, BUFFER_COLUMNS)
        if buff_mode == "w":
            writer.writeheader()

        with (
            ThreadPoolExecutor(max_workers=args.threads) as executor,
            requests.Session() as session,
        ):
            futures = {}
            for cat in category_prompts:
                for sci_name, row in in_data.items():
                    if not row["target"] or (sci_name, cat.name) in already_read:
                        continue
                    future = executor.submit(
                        call_model,
                        model_args,
                        sci_name,
                        cat,
                        row["target"],
                        session,
                    )
                    futures[future] = sci_name

            with tqdm(total=len(futures)) as pbar:
                for future in as_completed(futures):
                    sci_name = futures[future]
                    result = future.result()
                    statuses[result["status"]] += 1
                    cat = result["category"]
                    writer.writerow(
                        {
                            "sci_name": sci_name,
                            "status": result["status"],
                            "category": cat,
                            "mentions": " | ".join(
                                f"{cat}: {r}" for r in result["mentions"]
                            ),
                        }
                    )
                    buff_fh.flush()
                    pbar.update(1)

    write_results(buff_file, args.out_csv, in_data)

    logging.info(f"There were {statuses['ERROR']} errors")
    log.job_elapsed(job_began)


def write_results(buff_file: Path, out_csv: Path, in_data: dict) -> None:
    results = defaultdict(dict)
    with buff_file.open() as buff_fh:
        reader = csv.DictReader(buff_fh)
        for row in reader:
            results[row["sci_name"]][row["category"]] = {
                "status": row["status"],
                "mentions": row["mentions"],
            }

    out_rows = []
    for sci_name, in_row in in_data.items():
        out_row = {k: v for k, v in in_row.items() if k in OUT_COLUMNS}
        result_dict = results[sci_name]
        status = True
        categories = []
        mentions = []
        for cat in CATEGORY_ORDER:
            if cat not in result_dict:
                continue
            result = result_dict[cat]
            if not result["mentions"]:
                continue
            categories.append(cat)
            mentions.append(result["mentions"])
            status &= result["status"] == "success"

        out_row["threat_status"] = "success" if status else "ERROR"
        out_row["threat_categories"] = " | ".join(categories)
        out_row["threat_category_count"] = len(categories)
        out_row["threat_mentions"] = " | ".join(mentions)
        out_rows.append(out_row)

    df = pd.DataFrame(out_rows, columns=OUT_COLUMNS, dtype=str)
    df.to_csv(out_csv, index=False)


def call_model(
    args: ModelArgs,
    sci_name: str,
    cat: CategoryPrompt,
    threats: str,
    session: requests.Session,
) -> dict:
    url = f"{args.api_host}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('LLM_API_KEY')}",
    }
    payload = {
        "model": args.model_id,
        "messages": [
            {"role": "system", "content": cat.prompt},
            {
                "role": "user",
                "content": (
                    f"Extract threats in category '{cat.name}' "
                    f"from this text:\n\n{threats}"
                ),
            },
        ],
        "response_format": cat.json_schema,
        "enable_thinking": False,
    }

    extracted = {}
    status = "success"

    try:
        response = session.post(
            url, headers=headers, json=payload, timeout=args.timeout
        )
        response.raise_for_status()
        result = response.json()

        content = result["choices"][0]["message"]["content"] or ""
        content = content.replace("```json", "").replace("```", "")
        extracted = json.loads(content)
        if not (
            isinstance(extracted, dict) and isinstance(extracted.get("mentions"), list)
        ):
            raise TypeError(f"unexpected response shape: {content[:200]}")

    except RequestException, JSONDecodeError, ValueError, TypeError:
        logging.exception(f"Parse error for: {sci_name} ({cat.name})")
        status = "ERROR"

    return {
        "category": cat.name,
        "status": status,
        "mentions": extracted.get("mentions") or [],
    }


def parse_args() -> argparse.Namespace:
    model_args = ModelArgs()
    arg_parser = argparse.ArgumentParser(
        description=textwrap.dedent(
            """Extract IUCN threat categories from NatureServe threat text."""
        ),
    )
    arg_parser.add_argument(
        "--in-csv",
        type=Path,
        required=True,
        metavar="PATH",
        help="""The CSV file containing the original threats.""",
    )
    arg_parser.add_argument(
        "--out-csv",
        type=Path,
        required=True,
        metavar="PATH",
        help="""Output threat categories to this CSV file.""",
    )
    arg_parser.add_argument(
        "--prompt-dir",
        type=Path,
        default=Path("prompts/iucn_threats"),
        metavar="path",
        help="""A directory of per-category prompt markdown files.
        (default: %(default)s)""",
    )
    arg_parser.add_argument(
        "--model-id",
        default=model_args.model_id,
        metavar="string",
        help="""Use this language model. (default: %(default)s)""",
    )
    arg_parser.add_argument(
        "--api-host",
        default=model_args.api_host,
        metavar="string",
        help="""URL for the LM model. (default %(default)s""",
    )
    arg_parser.add_argument(
        "--threads",
        type=int,
        default=model_args.threads,
        metavar="int",
        help="""How many parallel threads to run. (default: %(default)s)""",
    )
    arg_parser.add_argument(
        "--timeout",
        type=int,
        default=model_args.timeout,
        metavar="int",
        help="""How long to wait for the LM to respond in seconds.
        (default: %(default)s)""",
    )
    arg_parser.add_argument(
        "--log-file",
        type=Path,
        metavar="string",
        help="""Append logging notices to this file. It also logs the script arguments
            so you may use this to keep track of what you did.""",
    )
    arg_parser.add_argument(
        "--notes",
        metavar="string",
        help="""Notes for logging. They only appear in the log file.""",
    )
    arg_parser.add_argument(
        "--limit",
        type=int,
        metavar="INT",
        help="""Limit to this many records (each record is up to 12 model calls).""",
    )
    args = arg_parser.parse_args()
    return args


if __name__ == "__main__":
    ARGS = parse_args()
    load_dotenv()
    classify_threats(ARGS)
