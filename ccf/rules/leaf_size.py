from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from spacy import registry
from spacy.language import Language
from traiter.pylib import term_util
from traiter.pylib.darwin_core import DarwinCore
from traiter.pylib.pattern_compiler import Compiler
from traiter.pylib.pipes import add
from traiter.pylib.rules.base import Base

from ccf.pylib.dimension import Dimension


@dataclass(eq=False)
class LeafSize(Base):
    # Class vars ----------
    terms = (Path(__file__).parent.parent / "terms" / "leaf_terms.csv",)
    parts: ClassVar[list[str]] = term_util.get_labels(terms)
    other: ClassVar[list[str]] = [t for t in parts if t != "leaf"]
    leaf: ClassVar[str] = "leaf"
    # ---------------------

    part: str | None = None
    units: str | None = None
    dims: list[Dimension] = field(default_factory=list)

    def to_dwc(self, dwc) -> DarwinCore:
        ...

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
                keep="leaf_size",
                on_match="leaf_size_match",
                decoder={
                    "leaf": {"ENT_TYPE": "leaf"},
                    "other": {"ENT_TYPE": {"IN": cls.other}},
                    "size": {"ENT_TYPE": "size"},
                },
                patterns=[
                    "leaf* size+",
                    "other* size+",
                ],
            ),
        ]

    @classmethod
    def leaf_size_match(cls, ent):
        dims = []
        units = ""
        part = "leaf"

        for e in ent.ents:
            if e.label_ == "size":
                dims = e._.trait.dims
                units = e._.trait.units

            elif e.label_ in cls.parts:
                part = e.label_

        trait = cls.from_ent(ent, part=part, dims=dims, units=units)
        return trait


@registry.misc("leaf_size_match")
def leaf_size_match(ent):
    return LeafSize.leaf_size_match(ent)
