from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from spacy.language import Language
from spacy.util import registry
from traiter.pylib import term_util
from traiter.pylib.pattern_compiler import Compiler
from traiter.pylib.pipes import add

from ccf.pylib.dimension import Dimension
from ccf.rules.base import Base


@dataclass(eq=False)
class FruitSize(Base):
    # Class vars ----------
    terms = (Path(__file__).parent / "terms" / "fruit_terms.csv",)
    parts: ClassVar[list[str]] = term_util.get_labels(terms)
    other: ClassVar[list[str]] = [t for t in parts if t != "fruit"]
    fruit: ClassVar[str] = "fruit"
    # ---------------------

    part: str | None = None
    units: str | None = None
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
                keep="fruit_size",
                on_match="fruit_size_match",
                decoder={
                    "fruit": {"ENT_TYPE": "fruit"},
                    "other": {"ENT_TYPE": {"IN": cls.other}},
                    "size": {"ENT_TYPE": "size"},
                },
                patterns=[
                    "fruit* size+",
                    "other* size+",
                ],
            ),
        ]

    @classmethod
    def fruit_size_match(cls, ent):
        dims = []
        units = ""
        part = "fruit"

        for e in ent.ents:
            if e.label_ == "size":
                dims = e._.trait.dims
                units = e._.trait.units

            elif e.label_ in cls.parts:
                part = e.label_

        trait = cls.from_ent(ent, part=part, dims=dims, units=units)
        return trait


@registry.misc("fruit_size_match")
def fruit_size_match(ent):
    return FruitSize.fruit_size_match(ent)
