from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from spacy.language import Language
from spacy.util import registry
from traiter.pipes import add
from traiter.pylib import term_util
from traiter.pylib.pattern_compiler import Compiler

from ccf.rules.base import Base


@dataclass(eq=False)
class Shape(Base):
    # Class vars ----------
    terms: ClassVar[Path] = Path(__file__).parent / "terms" / "shape_terms.csv"
    replace: ClassVar[dict[str, str]] = term_util.look_up_table(terms, "replace")
    # ---------------------

    shape: str = ""

    @classmethod
    def pipe(cls, nlp: Language):
        add.term_pipe(nlp, name="shape_terms", path=cls.terms)
        # add.debug_tokens(nlp)  # ##########################################
        add.trait_pipe(
            nlp,
            name="shape_patterns",
            compiler=cls.shape_patterns(),
        )
        add.cleanup_pipe(nlp, name="shape_cleanup")

    @classmethod
    def shape_patterns(cls):
        return [
            Compiler(
                label="shape",
                on_match="shape_match",
                decoder={
                    "shape": {"ENT_TYPE": "shape_term"},
                },
                patterns=[
                    " shape+ ",
                ],
            ),
        ]

    @classmethod
    def shape_match(cls, ent):
        text = ent.text.lower()
        return cls.from_ent(ent, shape=cls.replace.get(text, text))


@registry.misc("shape_match")
def shape_match(ent):
    return Shape.shape_match(ent)
