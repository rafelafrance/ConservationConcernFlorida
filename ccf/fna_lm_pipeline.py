#!/usr/bin/env python3

import argparse
import json
import textwrap
from pathlib import Path

import dspy
from pylib import log
from pylib.lm_data import PROMPT, Instance, Score, TraitExtractor, summarize_scores
from rich import print as rprint

# from pprint import pp


def main(args):
    log.started()

    with args.examples.open() as f:
        example_data = json.load(f)

    instances = [Instance.dict_to_instance(d) for d in example_data]

    lm = dspy.LM(args.model, api_base=args.api_base, api_key=args.api_key)
    dspy.configure(lm=lm)

    trait_extractor = dspy.Predict(TraitExtractor)
    # trait_extractor = dspy.ChainOfThought(TraitExtractor)

    scores = []

    instances = instances[: args.limit] if args.limit else instances

    for i, instance in enumerate(instances, 1):
        rprint(f"[blue]{'=' * 80}")
        rprint(f"[blue]{i} {instance.taxon}")

        print()
        rprint(f"[blue]{instance.text}")
        print()

        pred = trait_extractor(text=instance.text, prompt=PROMPT)

        score = Score.score_instance(instance=instance, predictions=pred.traits)
        score.display()
        scores.append(score)

    summarize_scores(scores)

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
        default="ollama_chat/gemma3:27b",
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
