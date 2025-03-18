#!/usr/bin/env python3

import argparse
import json
import random
import textwrap
from pathlib import Path

import dspy
from dspy.evaluate import Evaluate
from pylib import log
from pylib.lm_data import PROMPT, Instance, TraitExtractor, score_prediction

# from pprint import pp


def main(args):
    log.started()

    random.seed(args.seed)

    with args.examples.open() as f:
        example_data = json.load(f)

    instances = [Instance.dict_to_instance(d) for d in example_data]
    dataset = example_splits(instances, args.train_split, args.dev_split)

    lm = dspy.LM(args.model, api_base=args.api_base, api_key=args.api_key)
    dspy.configure(lm=lm)

    trait_extractor = dspy.Predict(TraitExtractor)

    evaluator = Evaluate(
        devset=dataset["dev"],
        metric=score_prediction,
        num_threads=1,
        display_progress=True,
        display_table=True,
    )

    evaluator(trait_extractor, devset=dataset["dev"])

    log.finished()


def example_splits(instances: list[Instance], train_split, dev_split):
    examples = [
        dspy.Example(text=i.text, prompt=PROMPT, traits=i.traits).with_inputs(
            "text", "prompt"
        )
        for i in instances
    ]
    random.shuffle(examples)

    total = len(examples)
    split1 = round(total * train_split)
    split2 = split1 + round(total * dev_split)

    dataset = {
        "train": examples[:split1],
        "dev": examples[split1:split2],
        "test": examples[split2:],
    }

    return dataset


def validate_splits(args: argparse.Namespace) -> None:
    splits_sum = 1.0
    split_min, split_max = 0.0, 1.0

    splits = (args.train_split, args.dev_split, args.test_split)

    if sum(splits) != splits_sum:
        msg = "train, dev, and test splits must sum to 1.0"
        raise ValueError(msg)

    if any(s < split_min or s > split_max for s in splits):
        msg = "All splits must be in the interval [0.0, 1.0]"
        raise ValueError(msg)


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
        "--train-split",
        type=float,
        default=0.1,
        metavar="FRACTION",
        help="""What fraction of records to use for training the model.
            (default: %(default)s)""",
    )

    arg_parser.add_argument(
        "--dev-split",
        type=float,
        default=0.5,
        metavar="FRACTION",
        help="""What fraction of records to use for scoring the model while training.
            (default: %(default)s)""",
    )

    arg_parser.add_argument(
        "--test-split",
        type=float,
        default=0.4,
        metavar="FRACTION",
        help="""What fraction of records to use for testing the model.
            (default: %(default)s)""",
    )

    arg_parser.add_argument(
        "--seed",
        type=int,
        default=2203673,
        help="""Seed for the random number generator.""",
    )

    args = arg_parser.parse_args()

    validate_splits(args)

    return args


if __name__ == "__main__":
    ARGS = parse_args()
    main(ARGS)
