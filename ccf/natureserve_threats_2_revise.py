#!/usr/bin/env python

import argparse
import csv
import json
import logging
import os
import textwrap
from collections import defaultdict
from dataclasses import dataclass
from json.decoder import JSONDecodeError
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from requests.exceptions import RequestException
from tqdm import tqdm

from ccf.pylib import log
from ccf.pylib import natureserve_threats as nt


@dataclass
class ModelArgs:
    model_id: str = "unsloth/gemma-4-31B-it-GGUF"
    api_host: str = "http://localhost:9931/v1"
    timeout: int = 300
    threads: int = 4


def revise_threats(args: argparse.Namespace) -> None:
    job_began = log.job_began(args.log_file, args=args)

    model_args = ModelArgs(
        model_id=args.model_id,
        api_host=args.api_host,
        timeout=args.timeout,
        threads=args.threads,
    )

    prompt = nt.load_prompt(args.prompt_path)

    already_revised, revised_mode = get_already_revised(args.out_csv)

    out_rows = read_data(args.in_csv, args.threat_csv)

    with args.out_csv.open(revised_mode) as out_fh, requests.Session() as session:
        writer = csv.DictWriter(out_fh, nt.OUT_COLUMNS)
        if revised_mode == "w":
            writer.writeheader()

        for row in tqdm(out_rows.values()):
            mentions = row["threat_mentions"].split(" | ")
            new_categories = set()
            new_mentions = []
            changed = []
            for mention in mentions:
                match = nt.MENTION_RE.search(mention)
                if not match:
                    continue

                threat_id, threat_name, threat = match.groups()
                if (row["Scientific Name"], threat) in already_revised:
                    continue

                category_id = call_revise_threat_model(
                    model_args, row["Scientific Name"], prompt, threat, session
                )

                if not category_id or not isinstance(category_id, (int, float)):
                    new_categories.add(f"{threat_id}. {threat_name}")
                    new_mentions.append((int(threat_id), mention))
                else:
                    category_id = int(category_id)
                    category = nt.CATEGORIES[category_id - 1]
                    new_categories.add(category)
                    new_mentions.append((category_id, f"{category}: {threat}"))
                    if int(threat_id) != category_id:
                        changed.append(f"{threat_id} -> {category}: {threat}")

            threat_categories = [c for c in nt.CATEGORIES if c in new_categories]
            row["threat_categories_revised"] = " | ".join(threat_categories)
            row["threat_category_count_revised"] = str(len(threat_categories))
            new_mentions = [m[1] for m in new_mentions]
            row["threat_mentions_revised"] = " | ".join(new_mentions)
            row["threat_category_changed"] = " | ".join(changed)
            writer.writerow(row)
            out_fh.flush()

    log.job_elapsed(job_began)


def read_data(in_csv: Path, threat_csv: Path) -> dict[str, dict]:
    threat_data = defaultdict(list)
    threats = pd.read_csv(threat_csv, dtype=str)
    threats = threats.fillna("").to_dict("records")
    for threat in threats:
        if threat["status"] == "success":
            threat_data[threat["Scientific Name"]].append(threat)

    out_rows = pd.read_csv(in_csv, dtype=str, usecols=nt.IN_COLUMNS)
    out_rows = out_rows.fillna("").to_dict("records")
    out_rows = [t for t in out_rows if t.get("Scientific Name")]
    for row in out_rows:
        row["target"] = "\n\n".join([t for f in nt.FIELDS if (t := row.get(f))]) or ""
    out_rows = {
        r["Scientific Name"]: r
        for r in out_rows
        if r["Scientific Name"] in threat_data
    }

    for sci_name, threats in threat_data.items():
        row = out_rows[sci_name]
        row["threat_status"] = "success"

        categories = set()
        threat_mentions = []
        for threat in threats:
            for mention in threat["mentions"].split("|"):
                cat = threat["category"]
                mention = mention.strip()
                if mention:
                    categories.add(cat)
                    threat_mentions.append(f"{cat}: {mention}")

        threat_categories = [c for c in nt.CATEGORIES if c in categories]
        row["threat_categories"] = " | ".join(sorted(threat_categories))
        row["threat_category_count"] = len(threat_categories)
        row["threat_mentions"] = " | ".join(threat_mentions)

    return out_rows


def get_already_revised(out_csv: Path) -> tuple:
    already_revised = set()
    revised_mode = "w"
    if out_csv.exists():
        revised_mode = "a"
        with out_csv.open() as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                mentions = row["threat_mentions"].split(" | ")
                for mention in mentions:
                    match = nt.MENTION_RE.search(mention)
                    if not mention:
                        continue
                    *_, threat = match.groups()
                    already_revised.add((row["Scientific Name"], threat))
    return already_revised, revised_mode


def call_revise_threat_model(
    args: ModelArgs,
    sci_name: str,
    prompt: nt.Prompt,
    mention: str,
    session: requests.Session,
) -> int:
    url = f"{args.api_host}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('LLM_API_KEY')}",
    }
    payload = {
        "model": args.model_id,
        "messages": [
            {"role": "system", "content": prompt.prompt},
            {
                "role": "user",
                "content": f"Classify the threat category of this text:\n\n{mention}",
            },
        ],
        "chat_template_kwargs": {"enable_thinking": False},
        "response_format": prompt.json_schema,
    }


    category = 0
    try:
        response = session.post(
            url, headers=headers, json=payload, timeout=args.timeout
        )
        response.raise_for_status()
        result = response.json()

        content = result["choices"][0]["message"]["content"] or ""
        content = content.replace("```json", "").replace("```", "")
        if content:
            extracted = json.loads(content)
            category = extracted.get("category", 0)

    except RequestException, JSONDecodeError, ValueError, TypeError:
        logging.exception(f"Parse error for {sci_name} ({mention})")

    return category


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
        "--threat-csv",
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
        "--prompt-path",
        type=Path,
        default=Path("prompts/iucn_threats_revised.md"),
        metavar="path",
        help="""A prompt used to revise threat categories. (default: %(default)s)""",
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
    revise_threats(ARGS)
