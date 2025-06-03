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
class FruitType(Base):
    # Class vars ----------
    terms: ClassVar[Path] = Path(__file__).parent / "terms" / "fruit_terms.csv"
    replace: ClassVar[dict[str, str]] = term_util.look_up_table(terms, "replace")
    # ---------------------

    fruit_type: str = ""

    @classmethod
    def pipe(cls, nlp: Language):
        add.term_pipe(nlp, name="fruit_type_terms", path=cls.terms)
        add.trait_pipe(
            nlp,
            name="fruit_type_patterns",
            compiler=cls.fruit_type_patterns(),
            overwrite=["fruit_type"],
        )
        add.cleanup_pipe(nlp, name="fruit_type_cleanup")

    @classmethod
    def fruit_type_patterns(cls):
        return [
            Compiler(
                label="fruit_type",
                on_match="fruit_type_match",
                decoder={
                    "type": {"ENT_TYPE": "fruit_type"},
                },
                patterns=[
                    " type+ ",
                ],
            ),
        ]

    @classmethod
    def fruit_type_match(cls, ent):
        text = ent.text.lower()
        return cls.from_ent(ent, fruit_type=cls.replace.get(text, text))


@registry.misc("fruit_type_match")
def fruit_type_match(ent):
    return FruitType.fruit_type_match(ent)
