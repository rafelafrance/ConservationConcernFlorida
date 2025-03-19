import json
import random
from pathlib import Path

import dspy
import Levenshtein

PROMPT = """
    What is the plant size,
    leaf shape, leaf length, leaf width, leaf thickness,
    seed length, seed width,
    fruit type, fruit length, fruit width,
    deciduousness, phenology, habitat, elevation?
    If it is not mentioned return an empty value.
    """


class TraitExtractor(dspy.Signature):
    """Analyze species descriptions and extract trait information."""

    # Input fields
    family: str = dspy.InputField(default="", desc="The family taxon")
    taxon: str = dspy.InputField(default="", desc="The taxon")
    text: str = dspy.InputField(default="", desc="The species description text")
    prompt: str = dspy.InputField(default="", desc="Extract these traits")

    # Output traits -- Just capturing the text for now
    plant_height: str = dspy.OutputField(default="", desc="The plant height")
    leaf_shape: str = dspy.OutputField(default="", desc="The leaf shape")
    leaf_length: str = dspy.OutputField(default="", desc="The leaf length")
    leaf_width: str = dspy.OutputField(default="", desc="The leaf width")
    leaf_thickness: str = dspy.OutputField(default="", desc="The leaf thickness")
    fruit_type: str = dspy.OutputField(default="", desc="The fruit type")
    fruit_length: str = dspy.OutputField(default="", desc="The fruit length")
    fruit_width: str = dspy.OutputField(default="", desc="The fruit width")
    seed_length: str = dspy.OutputField(default="", desc="The seed length")
    seed_width: str = dspy.OutputField(default="", desc="The seed witdth")
    deciduousness: str = dspy.OutputField(default="", desc="The plant's deciduousness")
    phenology: str = dspy.OutputField(default="", desc="The phenology")
    habitat: str = dspy.OutputField(default="", desc="The habitat")
    elevation: str = dspy.OutputField(default="", desc="The elevation")


TRAIT_FIELDS = [
    t for t in vars(TraitExtractor()) if t not in ("family", "taxon", "text", "prompt")
]


def dict2example(dct: dict[str, str]) -> dspy.Example:
    example = dspy.Example(
        text=dct["text"], family=dct["family"], taxon=dct["taxon"], prompt=PROMPT
    ).with_inputs("family", "taxon", "text", "prompt")

    for fld in TRAIT_FIELDS:
        setattr(example, fld, dct[fld])
    return example


def read_examples(example_json: Path) -> list[dspy.Example]:
    with example_json.open() as f:
        example_data = json.load(f)
    examples = [dict2example(d) for d in example_data]
    return examples


def split_examples(examples: list[dspy.Example], train_split: float, dev_split: float):
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


def score_prediction(example: dspy.Example, prediction: dspy.Prediction, trace=None):
    """Score predictions from DSPy."""
    total_score: float = 0.0

    for fld in TRAIT_FIELDS:
        true = getattr(example, fld)
        pred = getattr(prediction, fld)

        value = Levenshtein.ratio(true, pred)
        total_score += value

    total_score /= len(TRAIT_FIELDS)
    return total_score
