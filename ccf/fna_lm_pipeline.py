#!/usr/bin/env python3

import argparse
import textwrap
from pathlib import Path
from pprint import pp

import dspy
from bs4 import BeautifulSoup
from pylib import log


class ExtractInfo(dspy.Signature):
    """Analyze species descriptions and extract trait information."""

    text: str = dspy.InputField()
    question: str = dspy.InputField()
    entities: list[dict[str, str]] = dspy.OutputField(desc="list of extracted traits")


def main(args):
    log.started()

    pages = sorted(args.html_dir.glob("*.html"))

    lm = dspy.LM(args.model, api_base=args.api_base, api_key=args.api_key)

    questions = [
        """ What is the plant size,
            leaf shape, leaf length, leaf width, leaf thickness,
            seed length, seed width,
            fruit type, fruit length, fruit width,
            deciduousness?
            If it is not mentioned return an empty value.
            """,
        # """ What is the fruit type?
        #     A fruit type is like (berry, pome, stone, achene, capsule, caryopsis,
        #         cypsela, drupe, follicle, hesperidia, legume, loment nut pepo, samara,
        #         schizocarp, silicle, siliqua, utricle).
        #     If it is not mentioned return an empty string.
        #     """,
    ]

    test = argparse.Namespace()
    test.aa = 10
    print(test)

    module = dspy.Predict(ExtractInfo)

    for page in pages[:10]:
        print("=" * 80)
        print(page.stem)

        with page.open() as f:
            text = f.read()

        soup = BeautifulSoup(text, features="lxml")

        treatment = soup.find("span", class_="statement")
        print(treatment)

        for quest in questions:
            dspy.configure(lm=lm)
            reply = module(text=treatment, question=quest)
            print(page.stem)
            pp(reply.entities)
            print()

    log.finished()


def parse_args():
    arg_parser = argparse.ArgumentParser(
        allow_abbrev=True,
        description=textwrap.dedent("Extract information from downloaded HTML files."),
    )

    arg_parser.add_argument(
        "--html-dir",
        type=Path,
        required=True,
        metavar="PATH",
        help="""Parse HTML files in this directory.""",
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
        help="""Key for the LM model.""",
    )

    args = arg_parser.parse_args()

    return args


if __name__ == "__main__":
    ARGS = parse_args()
    main(ARGS)
