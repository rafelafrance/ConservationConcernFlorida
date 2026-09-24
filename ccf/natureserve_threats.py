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
from datetime import datetime
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

COLUMNS = (
    [
        "Scientific Name",
        "Order",
        "Family",
        "Genus",
        "NatureServe Unique Identifier",
        "Global Status",
        "Global Status (Rounded)",
    ]
    + [
        column
        for field in FIELDS
        for column in (
            field,
            f"{field}_status",
            f"{field}_categories",
            f"{field}_category_count",
            f"{field}_mentions",
        )
    ]
    + [
        "Summary_categories",
        "Summary_category_count",
        "Summary_mentions",
        "elapsed",
    ]
)

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

CSV_COLUMNS = [
    "Scientific Name",
    "Order",
    "Family",
    "Genus",
    "NatureServe Unique Identifier",
    "Global Status",
    "Global Status (Rounded)",
    *FIELDS,
]


@dataclass
class ModelArgs:
    prompt: str = ""
    json_schema: str = ""
    model_id: str = "unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL"
    api_host: str = "http://localhost:9931/v1"
    temperature: float = 0.3
    max_tokens: int | None = None
    reasoning_effort: str = "none"
    timeout: int = 300
    threads: int = 1


def classify_threats(args: argparse.Namespace) -> None:
    job_began = log.job_began(args.log_file, args=args)

    threats = pd.read_csv(args.in_csv, dtype=str, usecols=CSV_COLUMNS)
    threats = threats.fillna("").to_dict("records")
    threats = threats[: args.limit]

    with args.prompt.open() as fin:
        prompt = fin.read()
        prompt = re.sub("^---$.*^---$", "", prompt, flags=re.MULTILINE | re.DOTALL)
        prompt = prompt.strip()
        match = re.search("```json(.+)```", prompt, flags=re.DOTALL)
        json_schema = match.group(1).strip()

    statuses = defaultdict(int)

    model_args = ModelArgs(
        prompt=prompt,
        json_schema=json_schema,
        model_id=args.model_id,
        api_host=args.api_host,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        reasoning_effort=args.reasoning_effort,
        timeout=args.timeout,
        threads=args.threads,
    )

    # Resume: reuse fields already written successfully and only call the
    # model for the rest, so an interrupted run can be re-run cheaply.
    done = load_done(args.out_csv)
    mode = "a" if done else "w"

    with args.out_csv.open(mode) as out_file:
        writer = csv.DictWriter(out_file, COLUMNS)
        if mode == "w":
            writer.writeheader()

        with (
            ThreadPoolExecutor(max_workers=args.threads) as executor,
            requests.Session() as session,
        ):
            futures = {}
            pending = defaultdict(set)
            results = defaultdict(dict)
            began_at = {}
            for idx, threat in enumerate(threats):
                name = threat.get("Scientific Name", "")
                for field in FIELDS:
                    row = done.get((name, field))
                    if row and row.get(f"{field}_status") == "success":
                        results[idx][field] = field_result_from_row(row, field)
                    else:
                        pending[idx].add(field)
                        began_at.setdefault(idx, datetime.now())
                        futures[
                            executor.submit(
                                call_model,
                                model_args,
                                threat,
                                field,
                                session,
                            )
                        ] = (idx, field)

            with tqdm(total=len(pending)) as pbar:
                for future in as_completed(futures):
                    idx, field = futures[future]
                    results[idx][field] = future.result()
                    statuses[results[idx][field]["status"]] += 1
                    pending[idx].discard(field)
                    if not pending[idx]:
                        pbar.update(1)
                        writer.writerow(
                            make_row(threats[idx], results[idx], began_at[idx])
                        )
                        out_file.flush()

    log.job_elapsed(job_began)


def load_done(out_csv: Path) -> dict[tuple[str, str], dict]:
    """Return {(Scientific Name, field): row} from a previous run's output."""
    if not out_csv.exists() or out_csv.stat().st_size == 0:
        return {}
    with out_csv.open() as fin:
        reader = csv.DictReader(fin)
        if reader.fieldnames != COLUMNS:
            return {}
        rows = list(reader)
        return {
            (row["Scientific Name"], field): row for field in FIELDS for row in rows
        }


def field_result_from_row(row: dict, field: str) -> dict:
    """Extract one field's classification columns from a previously written row."""
    return {
        "status": row.get(f"{field}_status", ""),
        "categories": row.get(f"{field}_categories", ""),
        "category_count": row.get(f"{field}_category_count", ""),
        "mentions": row.get(f"{field}_mentions", ""),
    }


def make_row(threat: dict, results: dict, began: datetime) -> dict:
    """Assemble one output row from the per-field results."""
    row = {
        "Scientific Name": threat.get("Scientific Name", ""),
        "Order": threat.get("Order", ""),
        "Family": threat.get("Family", ""),
        "Genus": threat.get("Genus", ""),
        "NatureServe Unique Identifier": threat.get(
            "NatureServe Unique Identifier", ""
        ),
        "Global Status": threat.get("Global Status", ""),
        "Global Status (Rounded)": threat.get("Global Status (Rounded)", ""),
    }
    for field in FIELDS:
        result = results[field]
        row[field] = threat.get(field, "")
        row[f"{field}_status"] = result["status"]
        row[f"{field}_categories"] = result["categories"]
        row[f"{field}_category_count"] = result["category_count"]
        row[f"{field}_mentions"] = result["mentions"]

    # Summary across all fields: union of categories (in IUCN order) and
    # mentions (deduplicated, prefixed with the source field).
    present = set()
    for field in FIELDS:
        if results[field]["status"] != "success":
            continue
        present.update(filter(None, results[field]["categories"].split(" | ")))
    row["Summary_categories"] = " | ".join(c for c in CATEGORY_ORDER if c in present)
    row["Summary_category_count"] = str(len(present))

    seen = set()
    summary_mentions = []
    for field in FIELDS:
        if results[field]["status"] != "success":
            continue
        for mention in filter(None, results[field]["mentions"].split(" | ")):
            if mention in seen:
                continue
            seen.add(mention)
            summary_mentions.append(f"{field}: {mention}")
    row["Summary_mentions"] = " | ".join(summary_mentions)

    row["elapsed"] = str(log.task_elapsed(began))
    return row


def call_model(
    args: ModelArgs,
    threat: dict,
    field: str,
    session: requests.Session,
) -> dict:
    began = datetime.now()

    text = threat.get(field, "").strip()

    if not text:
        return {
            "status": "success",
            "categories": "",
            "category_count": "0",
            "mentions": "",
        }

    url = f"{args.api_host}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('LLM_API_KEY')}",
    }
    payload = {
        "model": args.model_id,
        "messages": [
            {"role": "system", "content": args.prompt},
            {"role": "user", "content": f"Extract threats from this text:\n\n{text}"},
        ],
        "response_format": args.json_schema,
        "reasoning_effort": args.reasoning_effort,
    }
    if args.temperature is not None:
        payload["temperature"] = args.temperature
    if args.max_tokens is not None:
        payload["max_tokens"] = args.max_tokens

    extracted = {}
    status = "ERROR"
    for _attempt in range(2):
        try:
            response = session.post(
                url, headers=headers, json=payload, timeout=args.timeout
            )
            response.raise_for_status()
            result = response.json()

            content = result["choices"][0]["message"]["content"] or ""
            content = content.replace("```json", "").replace("```", "")
            extracted = json.loads(content)

            status = "success"

        except RequestException, JSONDecodeError, ValueError:
            logging.exception(f"Parse error for: {threat['Scientific Name']} [{field}]")
            status = "ERROR"
            break

        # An all-false verdict on non-empty text is often an intermittent
        # model miss; retry once before accepting it.
        if any(isinstance(v, dict) and v.get("present") for v in extracted.values()):
            break

    categories = []
    mentions = []
    for name in CATEGORY_ORDER:
        value = extracted.get(name)
        if not isinstance(value, dict):
            continue
        if value.get("present"):
            categories.append(name)
        mentions += [f"{name}: {m}" for m in value.get("mentions") or []]

    return {
        "status": status,
        "categories": " | ".join(categories),
        "category_count": str(len(categories)),
        "mentions": " | ".join(mentions),
        "elapsed": str(log.task_elapsed(began)),
    }


def parse_args() -> argparse.Namespace:
    model_args = ModelArgs()
    arg_parser = argparse.ArgumentParser(
        description=textwrap.dedent("""Download data from the NatureServe website."""),
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
        "--prompt",
        type=Path,
        default="prompts/iucn_threats.md",
        metavar="path",
        help="""A markdown file with a prompt and list of fields to parse.""",
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
        "--temperature",
        type=float,
        default=model_args.temperature,
        metavar="float",
        help="""Model's temperature. Low but non-zero so the all-false
            retry can produce a different answer. (default: %(default)s)""",
    )
    arg_parser.add_argument(
        "--max-tokens",
        type=int,
        metavar="int",
        help="""The OCR model's response maximum tokens.
            I use this to truncate model loops.""",
    )
    arg_parser.add_argument(
        "--reasoning-effort",
        choices=["none", "low", "medium", "high"],
        default=model_args.reasoning_effort,
        metavar="{none,low,medium,high}",
        help="""The model's reasoning effort. "
        "Use none for bulk runs; medium for evaluation subsets. "
        "(default: %(default)s)""",
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
        help="""Limit to this many records (each record is up to 4 model calls).""",
    )
    args = arg_parser.parse_args()
    return args


if __name__ == "__main__":
    ARGS = parse_args()
    load_dotenv()
    classify_threats(ARGS)
