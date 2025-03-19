from dataclasses import dataclass, field, make_dataclass

import dspy
import Levenshtein
from rich import print as rprint

from ccf.pylib.trait_extractor import TRAIT_FIELDS

Traits = make_dataclass(
    "Traits",
    [(f, str, field(default="")) for f in TRAIT_FIELDS],
)

TraitScores = make_dataclass(
    "TraitScores",
    [(f, float, field(default=0.0)) for f in TRAIT_FIELDS],
)


@dataclass
class TrackScores:
    family: str = ""
    taxon: str = ""
    total: float = 0.0
    text: str = ""
    total_score: float = 0.0
    trues: Traits = field(default_factory=Traits)  # type: ignore [reportGeneralTypeIssues]
    preds: Traits = field(default_factory=Traits)  # type: ignore [reportGeneralTypeIssues]
    scores: TraitScores = field(default_factory=TraitScores)  # type: ignore [reportGeneralTypeIssues]

    @classmethod
    def track_scores(cls, *, example: dspy.Example, prediction: dspy.Prediction):
        """Save the score results for each trait field."""
        score = cls(family=example.family, taxon=example.taxon)

        for fld in TRAIT_FIELDS:
            true = getattr(example, fld)
            pred = getattr(prediction, fld)

            setattr(score.trues, fld, true)
            setattr(score.preds, fld, pred)

            value = Levenshtein.ratio(true, pred)
            setattr(score.scores, fld, value)
            score.total_score += value

        score.total_score /= len(TRAIT_FIELDS)

        return score

    def display(self) -> None:
        for fld in TRAIT_FIELDS:
            true = getattr(self.trues, fld)
            pred = getattr(self.preds, fld)
            true_folded = true.casefold()
            pred_folded = pred.casefold()
            if true_folded == pred_folded:
                rprint(f"[green]{fld}: {true}")
            else:
                rprint(f"[red]{fld}: {true} [/red]!= [yellow]{pred}")
        rprint(f"[blue]Score = {(self.total_score * 100.0):6.2f}")

    @staticmethod
    def summarize_scores(scores: list) -> None:
        rprint("\n[blue]Score summary:\n")
        count = float(len(scores))
        for fld in TRAIT_FIELDS:
            score: float = sum(getattr(s.scores, fld) for s in scores)
            rprint(f"[blue]{fld + ':':<16} {score / count * 100.0:6.2f}")
        total_score = sum(s.total_score for s in scores) / count * 100.0
        rprint(f"\n[blue]{'Total Score:':<16} {total_score:6.2f}\n")
