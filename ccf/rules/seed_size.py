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
class SeedSize(Base):
    # Class vars ----------
    terms = (Path(__file__).parent / "terms" / "seed_terms.csv",)
    parts: ClassVar[list[str]] = term_util.get_labels(terms)
    other: ClassVar[list[str]] = [t for t in parts if t != "seed"]
    seed: ClassVar[str] = "seed"
    # ---------------------

    part: str | None = None
    units: str | None = None
    dims: list[Dimension] = field(default_factory=list)

    @classmethod
    def pipe(cls, nlp: Language):
        add.term_pipe(nlp, name="seed_size_terms", path=cls.terms)
        # add.debug_tokens(nlp)  # ##########################################
        add.trait_pipe(
            nlp,
            name="seed_size_patterns",
            compiler=cls.seed_size_patterns(),
            overwrite=["size"],
        )

        add.cleanup_pipe(nlp, name="seed_size_cleanup")

    @property
    def dimensions(self):
        return tuple(d.dim for d in self.dims)

    @classmethod
    def seed_size_patterns(cls):
        return [
            Compiler(
                label="seed_size",
                keep="seed_size",
                on_match="seed_size_match",
                decoder={
                    "seed": {"ENT_TYPE": "seed"},
                    "other": {"ENT_TYPE": {"IN": cls.other}},
                    "size": {"ENT_TYPE": "size"},
                },
                patterns=[
                    "seed* size+",
                    "other* size+",
                ],
            ),
        ]

    @classmethod
    def seed_size_match(cls, ent):
        dims = []
        units = ""
        part = "seed"

        for e in ent.ents:
            if e.label_ == "size":
                dims = e._.trait.dims
                units = e._.trait.units

            elif e.label_ in cls.parts:
                part = e.label_

        trait = cls.from_ent(ent, part=part, dims=dims, units=units)
        return trait


@registry.misc("seed_size_match")
def seed_size_match(ent):
    return SeedSize.seed_size_match(ent)
