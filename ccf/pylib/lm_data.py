from dataclasses import asdict, dataclass

import dspy
from Levenshtein import ratio
from rich import print as rprint

PROMPT = """
    What is the plant size,
    leaf shape, leaf length, leaf width, leaf thickness,
    seed length, seed width,
    fruit type, fruit length, fruit width,
    deciduousness, phenology, habitat, elevation?
    If it is not mentioned return an empty value.
    """


@dataclass
class Traits:
    plant_height: str = ""
    leaf_shape: str = ""
    leaf_length: str = ""
    leaf_width: str = ""
    leaf_thickness: str = ""
    fruit_type: str = ""
    fruit_length: str = ""
    fruit_width: str = ""
    seed_length: str = ""
    seed_width: str = ""
    deciduousness: str = ""
    phenology: str = ""
    habitat: str = ""
    elevation: str = ""


@dataclass
class Example(Traits):
    taxon: str = ""
    text: str = ""
    score: float = 0.0


TRAIT_FIELDS = list(asdict(Traits()).keys())
EXAMPLE_FIELDS = list(asdict(Example()).keys())


def score_example(trues, preds) -> float:
    score = 0.0

    for field in TRAIT_FIELDS:
        true = getattr(trues, field)
        pred = getattr(preds, field)

        score += ratio(true, pred)

    score /= len(TRAIT_FIELDS)

    return score


def dict_to_example(dct):
    example = Example()
    for field in EXAMPLE_FIELDS:
        setattr(example, field, dct.get(field, ""))
    return example


class ExtractInfo(dspy.Signature):
    """Analyze species descriptions and extract trait information."""

    text: str = dspy.InputField(desc="the species description text")
    prompt: str = dspy.InputField(desc="extract these traits")
    traits: Traits = dspy.OutputField(desc="the extracted traits")


def display_results(trues: Example, preds: Example):
    for field in TRAIT_FIELDS:
        true = getattr(trues, field)
        pred = getattr(preds, field)
        true_folded = true.casefold()
        pred_folded = pred.casefold()
        if true_folded == pred_folded and true == "":
            rprint(f"[yellow]{field}:")
        elif true_folded == pred_folded:
            rprint(f"[green]{field}: {true}")
        else:
            rprint(f"[red]{field}: {true} != {pred}")
    rprint(f"[blue]Score = {score_example(trues, preds):0.4f}")
