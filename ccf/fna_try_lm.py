#!/usr/bin/env python3

import argparse
import textwrap
from pathlib import Path

import dspy
from pylib import log
from pylib import track_scores as ts
from pylib import trait_extractor as te
from rich import print as rprint

# from pprint import pp


def main(args):
    log.started()

    examples = te.read_examples(args.examples_json)
    examples = examples[: args.limit] if args.limit else examples

    lm = dspy.LM(
        args.model, api_base=args.api_base, api_key=args.api_key, cache=args.no_cache
    )
    dspy.configure(lm=lm)

    trait_extractor = dspy.Predict(te.TraitExtractor)
    # trait_extractor = dspy.ChainOfThought(TraitExtractor)

    scores = []

    for i, example in enumerate(examples, 1):
        rprint(f"[blue]{'=' * 80}")
        rprint(f"[blue]{i} {example.family}")
        rprint(f"[blue]{i} {example.taxon}")

        print()
        rprint(f"[blue]{example.text}")
        print()

        pred = trait_extractor(
            family=example.family,
            taxon=example.taxon,
            text=example.text,
            prompt=te.PROMPT,
        )

        score = ts.TrackScores.track_scores(example=example, prediction=pred)
        score.display()

        scores.append(score)

    ts.TrackScores.summarize_scores(scores)

    log.finished()


def parse_args():
    arg_parser = argparse.ArgumentParser(
        allow_abbrev=True,
        description=textwrap.dedent("Extract information from downloaded HTML files."),
    )

    arg_parser.add_argument(
        "--examples-json",
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

    arg_parser.add_argument(
        "--no-cache",
        action="store_false",
        help="""Turn off caching for the model.""",
    )

    args = arg_parser.parse_args()

    return args


if __name__ == "__main__":
    ARGS = parse_args()
    main(ARGS)
