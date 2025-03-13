from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from spacy.language import Language
from spacy.util import registry
from traiter.pylib.pattern_compiler import Compiler
from traiter.pylib.pipes import add

from ccf.rules.base import Base


@dataclass(eq=False)
class LeafDuration(Base):
    # Class vars ----------
    terms: ClassVar[Path] = Path(__file__).parent / "terms" / "leaf_terms.csv"
    # ---------------------

    leaf_duration: str = ""

    @classmethod
    def pipe(cls, nlp: Language):
        add.term_pipe(nlp, name="leaf_duration_terms", path=cls.terms)
        add.trait_pipe(
            nlp,
            name="leaf_duration_patterns",
            compiler=cls.leaf_duration_patterns(),
            overwrite=["leaf_duration"],
        )
        add.cleanup_pipe(nlp, name="leaf_duration_cleanup")

    @classmethod
    def leaf_duration_patterns(cls):
        return [
            Compiler(
                label="leaf_duration",
                on_match="leaf_duration_match",
                keep="leaf_duration",
                decoder={
                    "duration": {"ENT_TYPE": "leaf_duration"},
                },
                patterns=[
                    " duration+ ",
                ],
            ),
        ]

    @classmethod
    def leaf_duration_match(cls, ent):
        return cls.from_ent(ent, leaf_duration=ent.text.lower())


@registry.misc("leaf_duration_match")
def leaf_duration_match(ent):
    return LeafDuration.leaf_duration_match(ent)
