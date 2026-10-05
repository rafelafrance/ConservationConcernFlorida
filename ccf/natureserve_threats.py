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
    "elapsed",
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
class ModelArgs:
    prompt: str = ""
    json_schema: str = ""
    model_id: str = "unsloth/Qwen3.8-27B-GGUF:Q8_K_XL"
    api_host: str = "http://localhost:9931/v1"
    timeout: int = 300
    threads: int = 1


def classify_threats(args: argparse.Namespace) -> None:
    job_began = log.job_began(args.log_file, args=args)

    in_data = pd.read_csv(args.in_csv, dtype=str, usecols=IN_COLUMNS)
    in_data = in_data.fillna("").to_dict("records")
    in_data = [t for t in in_data if t.get("Scientific Name")]
    in_data = in_data[: args.limit]
    for threat in in_data:
        threat["target"] = (
            "\n\n".join([t for f in FIELDS if (t := threat.get(f))]) or ""
        )
    threats = {t["Scientific Name"]: t for t in in_data}

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
        timeout=args.timeout,
        threads=args.threads,
    )

    with args.out_csv.open("w") as out_file:
        writer = csv.DictWriter(out_file, OUT_COLUMNS)
        writer.writeheader()

        with (
            ThreadPoolExecutor(max_workers=args.threads) as executor,
            requests.Session() as session,
        ):
            futures = {
                executor.submit(
                    call_model,
                    model_args,
                    sci_name,
                    threat["target"],
                    session,
                ): threat
                for sci_name, threat in threats.items()
            }

            with tqdm(total=len(threats)) as pbar:
                for future in as_completed(futures):
                    result = future.result()
                    statuses[result["threat_status"]] += 1
                    in_row = futures[future]
                    out_row = {
                        k: v for k, v in (in_row | result).items() if k in OUT_COLUMNS
                    }
                    pbar.update(1)
                    writer.writerow(out_row)
                    out_file.flush()

    logging.info(f"There were {statuses['ERROR']} errors")
    log.job_elapsed(job_began)


def call_model(
    args: ModelArgs,
    sci_name: str,
    threats: str,
    session: requests.Session,
) -> dict:
    began = datetime.now()

    if not threats:
        return {
            "threat_status": "success",
            "threat_categories": "",
            "threat_category_count": "0",
            "threat_mentions": "",
            "elapsed": "0",
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
            {
                "role": "user",
                "content": f"Extract threats from this text:\n\n{threats}",
            },
        ],
        "response_format": args.json_schema,
        "enable_thinking": False,
    }

    extracted = {}

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
        logging.exception(f"Parse error for: {sci_name}")
        status = "ERROR"

    categories = {}
    mentions = []
    for name in CATEGORY_ORDER:
        value = extracted.get(name)
        if not isinstance(value, dict):
            continue
        if value.get("present"):
            categories[name] = 1
        mentions += [f"{name}: {m}" for m in value.get("mentions") or []]

    return {
        "threat_status": status,
        "threat_categories": " | ".join(categories.keys()),
        "threat_category_count": str(len(categories)),
        "threat_mentions": " | ".join(mentions),
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
