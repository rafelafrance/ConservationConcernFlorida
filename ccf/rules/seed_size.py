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
class SeedSize(Base):
    # Class vars ----------
    terms: ClassVar[Path] = Path(__file__).parent / "terms" / "seed_terms.csv"
    replace: ClassVar[dict[str, str]] = term_util.look_up_table(terms, "replace")
    # ---------------------

    part: str | None = None
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
                on_match="seed_size_match",
                decoder={
                    "seed": {"ENT_TYPE": "seed_term"},
                    "part": {"ENT_TYPE": "seed_part"},
                    "size": {"ENT_TYPE": "size"},
                },
                patterns=[
                    "seed+ size+",
                    "part+ size+",
                ],
            ),
        ]

    @classmethod
    def seed_size_match(cls, ent):
        dims = []
        part = ""

        for e in ent.ents:
            if e.label_ == "size":
                dims = e._.trait.dims

            elif e.label_ in ("seed_term", "seed_part"):
                text = e.text.lower()
                part = cls.replace.get(text, text)

        trait = cls.from_ent(ent, part=part, dims=dims)
        return trait


@registry.misc("seed_size_match")
def seed_size_match(ent):
    return SeedSize.seed_size_match(ent)
