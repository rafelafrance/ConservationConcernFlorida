#!/usr/bin/env python3

import argparse
import json
import textwrap
from pathlib import Path

import dspy
from pylib import log
from pylib.lm_data import (
    PROMPT,
    ExtractInfo,
    dict_to_example,
    display_results,
    score_example,
)


def main(args):
    log.started()

    with args.examples.open() as f:
        example_data = json.load(f)

    examples = [dict_to_example(d) for d in example_data]

    lm = dspy.LM(args.model, api_base=args.api_base, api_key=args.api_key)
    dspy.configure(lm=lm)
    module = dspy.Predict(ExtractInfo)

    examples = examples[: args.limit] if args.limit else examples
    for example in examples:
        print("=" * 80)
        print(example.taxon)

        print()
        print(example.text)
        print()

        pred = module(text=example.text, prompt=PROMPT)
        example.score = score_example(example, pred.traits)
        display_results(example, pred.traits)

    total_score = sum(e.score for e in examples)
    avg_score = total_score / len(examples)
    print(f"Average score = {avg_score:0.4f}")

    log.finished()


def parse_args():
    arg_parser = argparse.ArgumentParser(
        allow_abbrev=True,
        description=textwrap.dedent("Extract information from downloaded HTML files."),
    )

    arg_parser.add_argument(
        "--examples",
        type=Path,
        required=True,
        metavar="PATH",
        help="""Get language model examples from this JSON file.""",
    )

    arg_parser.add_argument(
        "--model",
        default="ollama_chat/qwq",
        help="""Use this LLM model. (default: %(default)s)""",
    )

    arg_parser.add_argument(
        "--api-base",
        default="http://localhost:11434",
        help="""URL for the LM model. (default: %(default)s)""",
    )

    arg_parser.add_argument(
        "--api-key",
        help="""Key for the LM provider.""",
    )

    arg_parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="""Limit to this many input examples.""",
    )

    args = arg_parser.parse_args()

    return args


if __name__ == "__main__":
    ARGS = parse_args()
    main(ARGS)
