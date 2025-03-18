from dataclasses import dataclass, field, fields, make_dataclass

import dspy
import Levenshtein
from pydantic import BaseModel
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
class Traits(BaseModel):
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


# I don't want to type in all of the trait fields again just to change the type to float
TraitScores = make_dataclass(
    "TraitScores",
    [(f.name, float, field(default=0.0)) for f in fields(Traits)],
)


@dataclass
class Instance(BaseModel):
    taxon: str = ""
    text: str = ""
    traits: Traits = field(default_factory=Traits)

    @classmethod
    def dict_to_instance(cls, dct):
        """Create an instance object from a dict, typically gotten from a JSON file."""
        instance = cls(taxon=dct["taxon"], text=dct["text"])
        for fld in fields(Traits):
            fld = fld.name
            setattr(instance.traits, fld, dct.get("traits", {}).get(fld, ""))
        return instance


@dataclass
class Score(BaseModel):
    taxon: str = ""
    text: str = ""
    total_score: float = 0.0
    trues: Traits = field(default_factory=Traits)
    preds: Traits = field(default_factory=Traits)
    scores: TraitScores = field(default_factory=TraitScores)  # type: ignore [reportGeneralTypeIssues]

    @classmethod
    def score_instance(cls, *, instance: Instance, predictions: Traits):
        """Create a score object from an instance object and LM predictions."""
        score = cls(taxon=instance.taxon)

        flds = [fld.name for fld in fields(Traits)]
        for fld in flds:
            true = getattr(instance.traits, fld)
            pred = getattr(predictions, fld)

            setattr(score.trues, fld, true)
            setattr(score.preds, fld, pred)

            value = Levenshtein.ratio(true, pred)
            setattr(score.scores, fld, value)
            score.total_score += value

        score.total_score /= len(flds)

        return score

    def display(self):
        flds = [fld.name for fld in fields(Traits)]
        for fld in flds:
            true = getattr(self.trues, fld)
            pred = getattr(self.preds, fld)
            true_folded = true.casefold()
            pred_folded = pred.casefold()
            if true_folded == pred_folded:
                rprint(f"[green]{fld}: {true}")
            else:
                rprint(f"[red]{fld}: {true} [/red]!= [yellow]{pred}")
        rprint(f"[blue]Score = {(self.total_score * 100.0):6.2f}")


def score_prediction(example: dspy.Example, prediction: dspy.Prediction, trace=None):
    """Score predictions from DSPy."""
    total_score: float = 0.0

    flds = [fld.name for fld in fields(Traits)]
    for fld in flds:
        true = getattr(example.traits, fld)
        pred = getattr(prediction.traits, fld)

        value = Levenshtein.ratio(true, pred)
        total_score += value

    total_score /= len(flds)
    return total_score


def summarize_scores(scores: list[Score]) -> None:
    rprint("\n[blue]Score summary:\n")
    count = float(len(scores))
    flds = [fld.name for fld in fields(Traits)]
    for fld in flds:
        score: float = sum(getattr(s.scores, fld) for s in scores)
        rprint(f"[blue]{fld + ':':<16} {score / count * 100.0:6.2f}")
    total_score = sum(s.total_score for s in scores) / count * 100.0
    rprint(f"\n[blue]{'Total Score:':<16} {total_score:6.2f}\n")


class TraitExtractor(dspy.Signature):
    """Analyze species descriptions and extract trait information."""

    text: str = dspy.InputField(desc="the species description text")
    prompt: str = dspy.InputField(desc="extract these traits")
    traits: Traits = dspy.OutputField(desc="the extracted traits")
