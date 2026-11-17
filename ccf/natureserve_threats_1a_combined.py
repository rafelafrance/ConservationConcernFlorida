#!/usr/bin/env python
import argparse
import csv
import json
import logging
import os
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
from ccf.pylib import natureserve_threats as nt


@dataclass
class ModelArgs:
    model_id: str = "unsloth/Qwen3.6-35B-A3B-MTP-GGUF"
    api_host: str = "http://localhost:9931/v1"
    timeout: int = 300
    threads: int = 4
    max_tokens: int | None = None


def classify_threats(args: argparse.Namespace) -> None:
    job_began = log.job_began(args.log_file, args=args)

    in_data = pd.read_csv(args.in_csv, dtype=str, usecols=nt.IN_COLUMNS)
    # TODO: Filter out records that were already done
    in_data = in_data.fillna("").to_dict("records")
    in_data = [t for t in in_data if t.get("Scientific Name")]
    in_data = in_data[: args.limit]
    for threat in in_data:
        threat["target"] = (
            "\n\n".join([t for f in nt.FIELDS if (t := threat.get(f))]) or ""
        )
    in_data = {t["Scientific Name"]: t for t in in_data}
    logging.info(f"Processing {len(in_data)} records")

    model_args = ModelArgs(
        model_id=args.model_id,
        api_host=args.api_host,
        timeout=args.timeout,
        threads=args.threads,
        max_tokens=args.max_tokens,
    )

    prompt = nt.load_prompt(args.prompt)

    out_mode = "w"  # TODO: Append if the file already has data

    with args.out_csv.open(out_mode) as out_fh:
        writer = csv.DictWriter(out_fh, nt.BUFFER_COLUMNS)
        if out_mode == "w":
            writer.writeheader()

        with (
            ThreadPoolExecutor(max_workers=args.threads) as executor,
            requests.Session() as session,
        ):
            futures = {}
            for sci_name, row in in_data.items():
                future = executor.submit(
                    call_model,
                    model_args,
                    sci_name,
                    prompt,
                    row["target"],
                    session,
                )
                futures[future] = sci_name

            statuses = defaultdict(int)

            with tqdm(total=len(futures)) as pbar:
                for future in as_completed(futures):
                    sci_name = futures[future]
                    result, status = future.result()
                    statuses[status] += 1

                    for cat, mention_dict in result.items():
                        mentions = " | ".join(mention_dict["mentions"])
                        writer.writerow(
                            {
                                "Scientific Name": sci_name,
                                "status": status,
                                "category": cat,
                                "mentions": mentions,
                            }
                        )
                    out_fh.flush()
                    pbar.update(1)

    logging.info(f"There were {statuses['success']} successes")
    logging.info(f"There were {statuses['ERROR']} errors")
    log.job_elapsed(job_began)


def call_model(
    args: ModelArgs,
    sci_name: str,
    prompt: nt.Prompt,
    threats: str,
    session: requests.Session,
) -> tuple[dict, str]:
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
                "content": (
                    f"Extract threats in category '{prompt.name}' "
                    f"from this text:\n\n{threats}"
                ),
            },
        ],
        "response_format": prompt.json_schema,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    if args.max_tokens is not None:
        payload["max_tokens"] = args.max_tokens

    url = f"{args.api_host}/chat/completions"
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

    except (RequestException, JSONDecodeError, ValueError, TypeError) as err:
        error = str(err)[:120]
        extracted = {"ERROR": {"mentions": [f"Error: {error}"]}}
        logging.error(f"Parse error for {sci_name}: {error}")
        status = "ERROR"

    return extracted, status


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
        "--prompt",
        type=Path,
        default=Path("prompts/iucn_threats.md"),
        metavar="path",
        help="""The prompt for classifying threats. (default: %(default)s)""",
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
        "--max-tokens",
        type=int,
        metavar="INT",
        help="""The model's response maximum tokens.""",
    )
    arg_parser.add_argument(
        "--log-file",
        type=Path,
        metavar="string",
        help="""Append logging notices to this file. It also logs the script arguments
            so you may use this to keep track of what you did.""",
    )
    arg_parser.add_argument(
        "--limit",
        type=int,
        metavar="INT",
        help="""Limit to this many records.""",
    )
    args = arg_parser.parse_args()
    return args


if __name__ == "__main__":
    ARGS = parse_args()
    load_dotenv()
    classify_threats(ARGS)
