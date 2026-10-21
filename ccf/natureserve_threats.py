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
    *IN_COLUMNS,
    "threat_status",
    "threat_categories",
    "threat_category_count",
    "threat_mentions",
    "threat_categories_revised",
    "threat_category_count_revised",
    "threat_mentions_revised",
    "threat_category_changed",
    "grazing_flag",
    "ORVs_flag",
    "trampling_flag",
    "trail_flag",
    "succession_flag",
    "erosion_flag",
    "fire_flag",
    "target",
]

BUFFER_COLUMNS = [
    "status",
    "Scientific Name",
    "category",
    "mentions",
]

CATEGORIES = [
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

FLAGS = {
    "erode": "erosion_flag",
    "eroded": "erosion_flag",
    "erosion": "erosion_flag",
    "fire": "fire_flag",
    "fires": "fire_flag",
    "wildfire": "fire_flag",
    "wildfires": "fire_flag",
    "graze": "grazing_flag",
    "grazed": "grazing_flag",
    "grazing": "grazing_flag",
    "orv": "ORVs_flag",
    "orvs": "ORVs_flag",
    "succession": "succession_flag",
    "trail": "trail_flag",
    "trample": "trampling_flag",
    "trampled": "trampling_flag",
    "trampling": "trampling_flag",
}


@dataclass
class Prompt:
    name: str
    prompt: str
    json_schema: str


@dataclass
class ModelArgs:
    model_id: str = "unsloth/Qwen3.8-27B-UD-Q8_K_XL"
    api_host: str = "http://localhost:9931/v1"
    timeout: int = 300
    threads: int = 1


def classify_threats(args: argparse.Namespace) -> None:
    job_began = log.job_began(args.log_file, args=args)

    in_data = read_in_data(args.in_csv, args.limit)

    buff_file = args.out_csv.with_stem(args.out_csv.stem + "_buffer")

    model_args = ModelArgs(
        model_id=args.model_id,
        api_host=args.api_host,
        timeout=args.timeout,
        threads=args.threads,
    )

    already_read, buff_mode = get_already_read(buff_file)

    write_buffer(
        model_args,
        in_data,
        buff_file,
        buff_mode,
        already_read,
        args.threads,
        args.prompt_dir,
    )

    out_rows = get_results(buff_file, in_data)
    set_flags(out_rows)

    revise_results(out_rows, model_args, args.prompt_path, args.threads)

    df = pd.DataFrame(out_rows, columns=OUT_COLUMNS, dtype=str)
    df.to_csv(args.out_csv, index=False)

    log.job_elapsed(job_began)


def read_in_data(in_csv: Path, limit: int | None) -> dict[str, dict]:
    in_data = pd.read_csv(in_csv, dtype=str, usecols=IN_COLUMNS)
    in_data = in_data.fillna("").to_dict("records")
    in_data = [t for t in in_data if t.get("Scientific Name")]
    in_data = in_data[:limit]
    for row in in_data:
        row["target"] = "\n\n".join([t for f in FIELDS if (t := row.get(f))]) or ""
    in_data = {t["Scientific Name"]: t for t in in_data}
    return in_data


def set_flags(in_data: dict) -> None:
    targets = set(FLAGS.keys())
    for row in in_data:
        words = set(row["target"].lower().split())
        for flag in words & targets:
            row[FLAGS[flag]] = "1"


def get_already_read(buff_file: Path) -> tuple:
    already_read = set()
    buff_mode = "w"
    if buff_file.exists():
        buff_mode = "a"
        with buff_file.open() as buff_csv:
            reader = csv.DictReader(buff_csv)
            already_read = {
                (r["Scientific Name"], r["category"])
                for r in reader
                if r["status"] == "success"
            }
    return already_read, buff_mode


def write_buffer(
    model_args: ModelArgs,
    in_data: dict,
    buff_file: Path,
    buff_mode: str,
    already_read: set,
    threads: int,
    prompt_dir: Path,
) -> None:
    category_prompts = load_category_prompts(prompt_dir)

    statuses = defaultdict(int)

    with buff_file.open(buff_mode) as buff_fh:
        writer = csv.DictWriter(buff_fh, BUFFER_COLUMNS)
        if buff_mode == "w":
            writer.writeheader()

        with (
            ThreadPoolExecutor(max_workers=threads) as executor,
            requests.Session() as session,
        ):
            futures = {}
            for cat in category_prompts:
                for sci_name, row in in_data.items():
                    if not row["target"] or (sci_name, cat.name) in already_read:
                        continue
                    future = executor.submit(
                        call_per_threat_model,
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
                    row = {
                        "Scientific Name": sci_name,
                        "status": result["status"],
                        "category": cat,
                        "mentions": " | ".join(
                            f"{cat}: {r.strip()}" for r in result["mentions"]
                        ),
                    }
                    writer.writerow(row)
                    buff_fh.flush()
                    pbar.update(1)

    logging.info(f"There were {statuses['ERROR']} errors")


def revise_results(
    out_rows: list[dict],
    model_args: ModelArgs,
    prompt_path: Path,
    threads: int,
) -> None:
    # return fuzz.partial_ratio(expect, actual) / 100.0
    prompt = load_prompt(prompt_path)

    with requests.Session() as session:
        for row in tqdm(out_rows):
            mentions = row["threat_mentions"].split(" | ")
            new_categories = set()
            new_mentions = []
            changed = []
            for mention in mentions:
                match = re.search(
                    r"^(\d+)\.\s*([^:]+?)\s*:\s*(.+)\s*$",
                    mention,
                    flags=re.DOTALL | re.MULTILINE,
                )
                if not match:
                    continue
                threat_id, threat_name, threat = match.groups()
                category_id = call_revise_threat_model(
                    model_args, row["Scientific Name"], prompt, threat, session
                )
                if not category_id or not isinstance(category_id, (int, float)):
                    new_categories.add(f"{threat_id}. {threat_name}")
                    new_mentions.append((int(threat_id), mention))
                else:
                    category_id = int(category_id)
                    category = CATEGORIES[category_id - 1]
                    new_categories.add(category)
                    new_mentions.append((category_id, f"{category}: {threat}"))
                    if int(threat_id) != category_id:
                        changed.append(f"{threat_id} -> {category}: {threat}")

            row["threat_categories_revised"] = " | ".join(sorted(new_categories))
            row["threat_category_count_revised"] = str(len(new_categories))
            new_mentions = [m[1] for m in sorted(new_mentions)]
            row["threat_mentions_revised"] = new_mentions
            row["threat_category_changed"] = " | ".join(changed)


def load_category_prompts(prompt_dir: Path) -> list[Prompt]:
    prompts = [load_prompt(path) for path in sorted(prompt_dir.glob("*.md"))]
    return prompts


def load_prompt(prompt_path: Path) -> Prompt:
    text = prompt_path.read_text()
    front = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    cat = re.search(r"^category:\s*(.+?)\s*$", front.group(1), flags=re.MULTILINE)
    name = cat.group(1).strip().strip('"')
    body = re.sub(r"^---$.*^---$", "", text, flags=re.MULTILINE | re.DOTALL).strip()
    schema = re.search(r"```json(.+)```", body, flags=re.DOTALL)
    prompt = Prompt(name, body, schema.group(1).strip())
    return prompt


def get_results(buff_file: Path, in_data: dict) -> list[dict]:
    results = defaultdict(dict)
    with buff_file.open() as buff_fh:
        reader = csv.DictReader(buff_fh)
        for row in reader:
            results[row["Scientific Name"]][row["category"]] = {
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
        for cat in CATEGORIES:
            if cat not in result_dict:
                continue
            result = result_dict[cat]
            status &= result["status"] == "success"
            mention = result["mentions"].strip()
            if not mention or result.get("status") != "success":
                continue
            categories.append(cat)
            mentions.append(mention)

        out_row["threat_status"] = "success" if status else "ERROR"
        out_row["threat_categories"] = " | ".join(categories)
        out_row["threat_category_count"] = len(categories)
        out_row["threat_mentions"] = " | ".join(mentions)
        out_rows.append(out_row)

    return out_rows


def call_revise_threat_model(
    args: ModelArgs,
    sci_name: str,
    prompt: Prompt,
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
        "reasoning": False,
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


def call_per_threat_model(
    args: ModelArgs,
    sci_name: str,
    cat: Prompt,
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
        "reasoning": False,
        "response_format": cat.json_schema,
    }

    status = "success"
    extracted = {}
    mentions = []

    try:
        response = session.post(
            url, headers=headers, json=payload, timeout=args.timeout
        )
        response.raise_for_status()
        result = response.json()

        content = result["choices"][0]["message"]["content"] or ""
        content = content.replace("```json", "").replace("```", "")
        extracted = json.loads(content)

        mentions = extracted.get("mentions")
        mentions = mentions if isinstance(mentions, list) else []

    except RequestException, JSONDecodeError, ValueError, TypeError:
        logging.exception(f"Parse error for {sci_name} ({cat.name})")
        status = "ERROR"

    return {
        "category": cat.name,
        "status": status,
        "mentions": mentions,
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
    classify_threats(ARGS)
