from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from spacy.language import Language
from spacy.util import registry
from traiter.pipes import add
from traiter.pylib import term_util
from traiter.pylib.pattern_compiler import Compiler

from ccf.pylib.dimension import Dimension
from ccf.rules.base import Base


@dataclass(eq=False)
class FruitSize(Base):
    # Class vars ----------
    terms: ClassVar[Path] = Path(__file__).parent / "terms" / "fruit_terms.csv"
    replace: ClassVar[dict[str, str]] = term_util.look_up_table(terms, "replace")
    # ---------------------

    part: str = ""
    dims: list[Dimension] = field(default_factory=list)

    @classmethod
    def pipe(cls, nlp: Language):
        add.term_pipe(nlp, name="fruit_size_terms", path=cls.terms)
        # add.debug_tokens(nlp)  # ##########################################
        add.trait_pipe(
            nlp,
            name="fruit_size_patterns",
            compiler=cls.fruit_size_patterns(),
            overwrite=["size"],
        )

        add.cleanup_pipe(nlp, name="fruit_size_cleanup")

    @property
    def dimensions(self):
        return tuple(d.dim for d in self.dims)

    @classmethod
    def fruit_size_patterns(cls):
        return [
            Compiler(
                label="fruit_size",
                on_match="fruit_size_match",
                decoder={
                    "type": {"ENT_TYPE": {"IN": ["fruit_type", "fruit"]}},
                    "size": {"ENT_TYPE": "size"},
                },
                patterns=[
                    "type+ size+",
                ],
            ),
        ]

    @classmethod
    def fruit_size_match(cls, ent):
        dims = []
        part = ""

        for e in ent.ents:
            if e.label_ == "size":
                dims = e._.trait.dims

            elif e.label_ in ("fruit_type", "fruit"):
                text = e.text.lower()
                part = cls.replace.get(text, text)

        trait = cls.from_ent(ent, part=part, dims=dims)
        return trait


@registry.misc("fruit_size_match")
def fruit_size_match(ent):
    return FruitSize.fruit_size_match(ent)
