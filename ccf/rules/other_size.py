from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from spacy.language import Language
from spacy.util import registry
from traiter.pipes import add
from traiter.pylib.pattern_compiler import Compiler

from ccf.pylib.dimension import Dimension
from ccf.rules.base import Base


@dataclass(eq=False)
class OtherSize(Base):
    # Class vars ----------
    terms: ClassVar[list[Path]] = [
        Path(__file__).parent / "terms" / "other_terms.csv",
        Path(__file__).parent / "terms" / "fruit_terms.csv",
        Path(__file__).parent / "terms" / "leaf_terms.csv",
        Path(__file__).parent / "terms" / "seed_terms.csv",
        Path(__file__).parent / "terms" / "shape_terms.csv",
    ]
    others: ClassVar[list[str]] = ["other_term", "fruit_part", "leaf_part", "seed_part"]
    # ---------------------

    part: str = None
    dims: list[Dimension] = field(default_factory=list)

    @classmethod
    def pipe(cls, nlp: Language):
        add.term_pipe(nlp, name="other_size_terms", path=cls.terms)
        # add.debug_tokens(nlp)  # ##########################################
        add.trait_pipe(
            nlp,
            name="other_size_patterns",
            compiler=cls.other_size_patterns(),
            overwrite=["size", *cls.others],
        )

        add.cleanup_pipe(nlp, name="other_size_cleanup")

    @property
    def dimensions(self):
        return tuple(d.dim for d in self.dims)

    @classmethod
    def other_size_patterns(cls):
        fill = ["PUNCT", "ADP", "CCONJ", "ADV", "PART", "ADJ"]
        return [
            Compiler(
                label="other_size",
                on_match="other_size_match",
                decoder={
                    "9.9": {"TEXT": {"REGEX": r"\d+(\.\d*)?"}},
                    "fill": {"POS": {"IN": fill}},
                    "other": {"ENT_TYPE": {"IN": cls.others}},
                    "shape": {"ENT_TYPE": "shape_term"},
                    "size": {"ENT_TYPE": "size"},
                },
                patterns=[
                    "other+ fill* size+",
                    "other+ fill* shape+ fill* size+",
                    "other+ fill* shape+ fill* shape+ fill* size+",
                    "other+ 9.9 fill+ size+",
                    "size+ other+",
                ],
            ),
        ]

    @classmethod
    def other_size_match(cls, ent):
        dims = []
        part = ""

        for e in ent.ents:
            if e.label_ == "size":
                dims = e._.trait.dims

            elif e.label_ in ("other_part", "other_term"):
                part = e.text.lower()

        trait = cls.from_ent(ent, part=part, dims=dims)
        return trait


@registry.misc("other_size_match")
def other_size_match(ent):
    return OtherSize.other_size_match(ent)
