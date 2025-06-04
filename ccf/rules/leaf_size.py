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
class LeafSize(Base):
    # Class vars ----------
    terms: ClassVar[Path] = Path(__file__).parent / "terms" / "leaf_terms.csv"
    replace: ClassVar[dict[str, str]] = term_util.look_up_table(terms, "replace")
    # ---------------------

    part: str = None
    dims: list[Dimension] = field(default_factory=list)

    @classmethod
    def pipe(cls, nlp: Language):
        add.term_pipe(nlp, name="leaf_size_terms", path=cls.terms)
        # add.debug_tokens(nlp)  # ##########################################
        add.trait_pipe(
            nlp,
            name="leaf_size_patterns",
            compiler=cls.leaf_size_patterns(),
            overwrite=["size"],
        )

        add.cleanup_pipe(nlp, name="leaf_size_cleanup")

    @property
    def dimensions(self):
        return tuple(d.dim for d in self.dims)

    @classmethod
    def leaf_size_patterns(cls):
        return [
            Compiler(
                label="leaf_size",
                on_match="leaf_size_match",
                decoder={
                    "leaf": {"ENT_TYPE": "leaf_term"},
                    "size": {"ENT_TYPE": "size"},
                },
                patterns=[
                    "leaf+ size+",
                ],
            ),
        ]

    @classmethod
    def leaf_size_match(cls, ent):
        dims = []
        part = ""

        for e in ent.ents:
            if e.label_ == "size":
                dims = e._.trait.dims

            elif e.label_ == "leaf_term":
                text = e.text.lower()
                part = cls.replace.get(text, text)

        trait = cls.from_ent(ent, part=part, dims=dims)
        return trait


@registry.misc("leaf_size_match")
def leaf_size_match(ent):
    return LeafSize.leaf_size_match(ent)
